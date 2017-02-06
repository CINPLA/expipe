from __future__ import division
import argparse
import neo
import numpy as np
import quantities as pq
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import datetime
import os
from ..statistics import *
from ..waveform import plot_waveforms, plot_amp_clusters
from ..tracking import *
from ..stimulus import plot_psth, epoch_overview
from expipe.data_writer import *
from ..time_frequency import plot_psd

class SpikesortSweep(object):
    """
    Visualize waveforms on respective channels

    Parameters
    ----------
    h5file : path to neo .h5 file to spikesort
    savepath : where to save output
    imgformat : figure file format
    n_cluster : number of clusters to separate

    Returns
    -------
    writes to file : sorted neo .h5 file and figures to savepath
    """
    def __init__(self, h5file, savepath=None, n_cluster=4, **kwargs):
        self.par = {'use_peak': True,
                    'use_peak_to_valley': True,
                    'n_pca': 3,
                    'n_ica': 3,
                    'n_haar': 3,
                    'sign': '+',
                    'n_cluster': n_cluster,
                    'n_iter': 100,
                    'imgformat': '.png',
                    'corr_bin_width': 0.01*pq.s,
                    'corr_limit': 1.*pq.s,
                    'isi_binsize': 1*pq.ms,
                    'isi_time_limit': 100*pq.ms,
                    'h5file': h5file,
                    'savepath': savepath}
        if kwargs:
            self.par.update(kwargs)
        self.kwargs = kwargs

        if not self.par['imgformat'][0] == '.':
            self.par['imgformat'] = '.'+self.par['imgformat']
        if savepath is None:
            savepath = os.getcwd()
        else:
            if savepath[-1] == os.path.sep:
                savepath = savepath[0:-1]
        path, file = os.path.split(h5file)
        filename = file.split('.')[0]
        savefile = savepath+os.path.sep+filename+'-sweep'
        if not os.path.exists(savefile):
            os.makedirs(savefile)
        self.par['savefile'] = savefile+os.path.sep+filename+'-sweep'

    def spikesort(self):
        from OpenElectrophy.spikesorting import SpikeSorter
        par = self.par
        r = neo.io.NeoHdf5IO(par['h5file'])
        blk = r.read_block()
        r.close()
        rcgs = blk.recordingchannelgroups
        for gidx, rcg in enumerate(rcgs):
            assert len(rcg.units) <= 1, 'more than one unit in %s' % rcg.name
            if rcg.name != 'T9':
                print('Clustering %s' % rcg.name)
                sps = SpikeSorter(rcg)
                # sps.PcaFeature(n_components = 4)
                sps.CombineFeature(use_peak=par['use_peak'],
                                   use_peak_to_valley=par['use_peak_to_valley'],
                                   n_pca=par['n_pca'], n_ica=par['n_ica'],
                                   n_haar=par['n_haar'], sign=par['sign'])
                sps.SklearnGaussianMixtureEm(n_cluster=par['n_cluster'],
                                             n_iter=par['n_iter'])

                rcg = sps.populate_recordingchannelgroup()
                blk.recordingchannelgroups[gidx] = rcg
        print('saving files in %s' % par['savefile'])
        blk.file_datetime = datetime.datetime.now()
        iom = neo.NeoHdf5IO(par['savefile']+'.h5')
        iom.save(blk)
        iom.close()
        yaml_singlefile_creator(par['savefile']+'.h5',
                                metadata=blk.annotations)

    def sweep(self):
        par = self.par
        r = neo.io.NeoHdf5IO(par['savefile']+'.h5')
        blk = r.read_block()
        r.close()
        rcgs = blk.recordingchannelgroups
        if 'tracking' in blk.annotations:
            tracking = Tracking(blk, par, **self.kwargs)
        else:
            tracking = False
        metadata = {'block': {'block_metadata': {'analysis_parameters': par}},
                    'units': {'path': [], 'unit_metadata': []}}
        for gidx, rcg in enumerate(rcgs):
            if rcg.name != 'T9':
                seg = blk.segments[0]
                colors = cm.rainbow(np.linspace(0, 1, len(rcg.units)))
                sptrs = []
                for uidx, unit in enumerate(rcg.units):
                    metadata['units']['path'].append(unit.hdf5_path)
                    tmpmetadata = {'unit_name': unit.name,
                                   'group_name': rcg.name,
                                   'unit': int(unit.name[9:]),
                                   'group': int(rcg.name[7:])}
                    print('Sweeping %s %s' % (rcg.name, unit.name))
                    color = colors[uidx]
                    sptr = unit.spiketrains[0]
                    sptrs.append(sptr)
                    figfilebase = par['savefile']+'-'+rcg.name+'-'+unit.name
                    if tracking:
                        tracking.stats(rcg, unit, tmpmetadata, figfilebase)

                    self.spikestats(rcg, unit, figfilebase, color)

                    if len(seg.epocharrays) == 1:
                        self.stimstats(seg.epocharrays[0], rcg, unit, figfilebase)
                    metadata['units']['unit_metadata'].append(tmpmetadata)
                fig8 = plt.figure()
                plot_amp_clusters(sptrs, colors=colors, fig=fig8, title=rcg.name)
                fig8.savefig(par['savefile']+'-'+rcg.name+'-clusters' +
                             par['imgformat'])
                plt.close(fig8)
        yaml_addon(par['savefile']+'.yaml', metadata=metadata)
        for ana in blk.segments[0].analogsignals:
            if ana.sampling_rate == 250:
                fig, ax = plt.subplots()
                plot_psd([ana], color='k', ax=ax, nperseg=1024)
                fig.savefig(par['savefile']+'-'+ana.name+'-psd-hem-' +
                            ana.annotations['hemisphere']+'-' +
                            str(ana.channel_index) +
                            par['imgformat'])
                plt.close(fig)


    def stimstats(self, epo, rcg, unit, figfilebase):
        par = self.par
        sptr = unit.spiketrains[0]
        epo_over = epoch_overview(epo)
        t_start = -np.round(epo_over.durations[0])
        t_stop = np.round(epo_over.durations[0])
        binsize = (abs(t_start) + abs(t_stop)) / 100.
        fig6 = plt.figure()
        plot_psth(sptr=sptr, epo=epo_over, t_start=t_start,
                  t_stop=t_stop, output='counts', binsize=binsize,
                  title='%s %s' % (rcg.name, unit.name), fig=fig6)
        fig6.savefig(figfilebase + '-stim-macro' + par['imgformat'])
        plt.close(fig6)

        fig7 = plt.figure()
        t_start = -np.round(epo.durations[0].rescale('ms'))*3  # FIXME is milliseconds always good?
        t_stop = np.round(epo.durations[0].rescale('ms'))*3
        binsize = (abs(t_start) + abs(t_stop)) / 100.
        plot_psth(sptr=sptr, epo=epo, t_start=t_start,
                  t_stop=t_stop, output='counts', binsize=binsize,
                  title='%s %s' % (rcg.name, unit.name), fig=fig7)
        fig7.savefig(figfilebase + '-stim-micro' + par['imgformat'])
        plt.close(fig7)

    def spikestats(self, rcg, unit, figfilebase, color):
        from .statistics.correlogram import correlogram
        par = self.par
        sptr = unit.spiketrains[0]
        title = rcg.name+' '+unit.name + ' N spikes = %i' % sptr.size
        fig2 = plt.figure()
        plot_waveforms(sptr=sptr, color=color, fig=fig2, title=title)
        fig2.savefig(figfilebase + '-waveform' + par['imgformat'])
        plt.close(fig2)
        fig3 = plt.figure()
        plot_amp_clusters([sptr], colors=[color], fig=fig3, title=title)
        fig3.savefig(figfilebase + '-cluster' + par['imgformat'])
        plt.close(fig3)

        fig4, ax4 = plt.subplots()
        bin_width = par['corr_bin_width'].rescale('s').magnitude
        limit = par['corr_limit'].rescale('s').magnitude
        count, bins = correlogram(t1=sptr.times.magnitude, t2=None,
                                  bin_width=bin_width, limit=limit,
                                  auto=True)
        ax4.bar(bins[:-1] + bin_width / 2., count, width=bin_width,
                color=color)
        ax4.set_xlim([-limit, limit])
        ax4.set_title(title)
        fig4.savefig(figfilebase + '-autocorr' + par['imgformat'])
        plt.close(fig4)

        fig5, ax5 = plt.subplots()
        plot_hist_isi(sptr.times, alpha=1, ax=ax5, binsize=par['isi_binsize'],
                      time_limit=par['isi_time_limit'], color=color)
        ax5.set_title(title)
        fig5.savefig(figfilebase + '-isi' + par['imgformat'])
        plt.close(fig5)


class Tracking(object):
    def __init__(self, blk, par, **kwargs):
        self.par = par
        par.update({'pos_fs': 100*pq.Hz,
                    'f_cut': 6*pq.Hz,
                    'ang_binsize': 2,
                    'spat_binsize': 0.01*pq.m,
                    'spat_smoothing': 0.02,
                    'grid_stepsize': 0.1*pq.m,
                    'box_size': 1*pq.m,
                    'convolve': True})
        if kwargs:
            par.update(kwargs)
        x1, y1, t1, x2, y2, t2 = get_raw_position(blk)
        x, y, t = select_best_position(x1, y1, t1, x2, y2, t2)
        self.x, self.y, self.t = interp_filt_position(x, y, t,
                                                      pos_fs=par['pos_fs'],
                                                      f_cut=par['f_cut'])
        self.angles, self.times = head_direction(x1, y1, x2, y2, t1,
                                                 return_rad=False)

    def stats(self, rcg, unit, metadata, figfilebase):
        sptr = unit.spiketrains[0]
        par = self.par
        rate_map, rate_bins = \
            spatial_rate_map(self.x, self.y, self.t, sptr,
                             binsize=par['spat_binsize'],
                             mask_unvisited=True,
                             smoothing=par['spat_smoothing'],
                             convolve=par['convolve'],
                             return_bins=True)
        G, acorr = gridness(rate_map, box_size=par['box_size'],
                            step_size=par['grid_stepsize'], return_acorr=True)
        ang_bin, ang_rate = head_direction_rate(sptr, self.angles,
                                                self.times,
                                                binsize=par['ang_binsize'])
        mean_ang, mean_vec_len = head_direction_stats(ang_bin, ang_rate)
        px = prob_dist(self.x, self.y, rate_bins)
        metadata.update({'information_rate': information_rate(rate_map, px),
                         'sparsity': sparsity(rate_map, px),
                         'selectivity': selectivity(rate_map, px),
                         'coeff_var': (coeff_var([sptr])[0]),
                         'gridness': G,
                         'hd_aveclen': mean_vec_len,
                         'avg_rate': sptr.size/sptr.duration})
        if G > 0.3 or mean_vec_len > 0.3 and sptr.size > 100:
            print('%s %s gridness = %.2f HD score = %.2f' %
                  (rcg.name, unit.name, G, mean_vec_len))
        fig1 = make_spatiality_overview(self.x, self.y, self.t, self.angles,
                                        self.times, unit, acorr=acorr, G=G,
                                        group_name=rcg.name, rate_map=rate_map)
        fig1.savefig(figfilebase + '-tracking' + par['imgformat'])
        plt.close(fig1)
