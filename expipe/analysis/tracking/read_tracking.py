def read_tracking(self, group):
        """
        Read tracking data_end
        """
        group = self._find_my_group(group, 'Position')
        if group is None:
            return None
        if not hasattr(self, '_segments'):
            self._get_channel_indexes()
        irr_signals = []
        for spot_group in group.values():
            times = spot_group["timestamps"]
            coords = spot_group["data"]
            irrsig = IrregularlySampledSignal(name=spot_group.name.split('/')[-1],
                                              signal=coords.data,
                                              times=times.data,
                                              units=coords.attrs["unit"],
                                              time_units=times.attrs["unit"],
                                              file_origin=spot_group.folder)
            irr_signals.append(irrsig)
            self._segments[spot_group.attrs['segment_id']].irregularlysampledsignals.append(irrsig)

        return irr_signals
