import properties
import numpy as np

from .Survey import BaseSurvey
from .Survey import BaseSrc
from .Utils import mkvc


class UncertaintyArray(properties.Array):

    class_info = 'a numpy, Zero or Identity array'

    @property
    def min(self):
        """minimum allowed value of the entries in the array
        """
        return getattr(self, '_min', None)

    @min.setter
    def min(self, value):
        assert isinstance(value, float), 'min must be a float'
        self._min = value

    def validate(self, instance, value):
        if isinstance(value, float):
            if self.min is not None:
                assert value >= self.min, (
                    'value must be larger than the minimum of {}, '
                    'the value provided was {}'.format(self.min, value)
                )
            return value
        elif isinstance(value, np.ndarray):
            assert np.all(value >= self.min), (
                'all values must be larger than the minimum of {}'.format(self.min)
            )
        return super(UncertaintyArray, self).validate(instance, value)


class Data(properties.HasProperties):
    """
    Data storage
    """

    dobs = properties.Array(
        "observed data",
        shape=('*',),
        required=True
    )

    # standard_deviation can be a float or an array
    standard_deviation = UncertaintyArray(
        "standard deviation of the data",
        shape=('*',),
        dtype=float,
        # min=0.0
    )

    # noise_floor can be a float or an array
    noise_floor = UncertaintyArray(
        "noise floor of the data",
        shape=('*',),
        dtype=float,
        # min=0.0
    )

    survey = properties.Instance(
        "a SimPEG survey object",
        BaseSurvey
    )

    uid = properties.Uuid("unique ID for the data")

    _data_dict = properties.Instance(
        "data dictionary so data can be accessed by [src, rx]. "
        "This stores the indicies in the data vector corresponding "
        "to each source receiver pair",
        dict,
    )

    def __init__(self, **kwargs):
        dobs = kwargs.pop('dobs', None)
        if dobs is not None:
            self.dobs = dobs
        super(Data, self).__init__(**kwargs)

    @properties.Array(
        """
        Data uncertainties. If a stardard deviation and noise floor are
        provided, the incertainty is

        ..code::

            data.uncertainty == (
                data.standard_deviation * np.absolute(data.dobs) +
                data.noise_floor
            )

        otherwise, the uncertainty can be set directly

        ..code::

            data.uncertainty = 0.05 * np.absolute(self.dobs) + 1e-12

        """
    )
    def uncertainty(self):
        if self.standard_deviation is None and self.noise_floor is None:
            raise Exception(
                "The standard_deviation and / or noise_floor must be set "
                "before asking for uncertainties. Alternatively, the "
                "uncertainty can be set directly"
            )

        uncert = np.zeros(self.nD)
        if self.standard_deviation is not None:
            uncert = uncert + self.standard_deviation * np.absolute(self.dobs)
        if self.noise_floor is not None:
            uncert = uncert + self.noise_floor

        return uncert

    @uncertainty.setter
    def uncertainty(self, value):
        del self.standard_deviation
        self.noise_floor = value

    @properties.validator('standard_deviation')
    def _validate_standard_deviation(self, change):
        if isinstance(change['value'], float):
            change['value'] = np.ones(self.nD) * change['value']
        elif isinstance(change['value'], np.ndarray):
            assert len(change['value']) == self.nD, (
                "standard_deviation must have the same length as the number "
                "of data ({}). The provided standard_deviation has length "
                "{}".format(
                    self.nD, len(change['value'])
                )
            )

    @properties.validator('noise_floor')
    def _validate_noise_floor(self, change):
        if isinstance(change['value'], float):
            change['value'] = np.ones(self.nD) * change['value']
        elif isinstance(change['value'], np.ndarray):
            assert len(change['value']) == self.nD, (
                "noise_floor must have the same length as the number of "
                "data ({}). The provided noise_floor has length {}".format(
                    self.nD, len(change['value'])
                )
            )

    @properties.observer('survey')
    def _create_data_dict(self, change):
        survey = change['value']
        self._data_dict = {}

        # create an empty dict associated with each source
        for src in survey.srcList:
            self._data_dict[src] = {}

        # loop over sources and find the associated data indices
        indBot, indTop = 0, 0
        for src in self.survey.srcList:
            for rx in src.rxList:
                indTop += rx.nD
                self._data_dict[src][rx] = np.arange(indBot, indTop)
                indBot += rx.nD

    @property
    def nD(self):
        return len(self.dobs)

    def _ensureCorrectKey(self, key):
        if type(key) is tuple:
            if len(key) is not 2:
                raise KeyError('Key must be [Src, Rx]')
            if key[0] not in self.survey.srcList:
                raise KeyError('Src Key must be a source in the survey.')
            if key[1] not in key[0].rxList:
                raise KeyError('Rx Key must be a receiver for the source.')
            return key
        if isinstance(key, BaseSrc):
            if key not in self.survey.srcList:
                raise KeyError('Key must be a source in the survey.')
            return key, None
        else:
            raise KeyError('Key must be [Src] or [Src,Rx]')

    def _set_data_properties(self, key, value, arr_name='dobs'):
        """
        Function to set data, standard_deviation or noise floor with
        a [src, rx] pair.

        """

        src, rx = self._ensureCorrectKey(key)
        assert rx is not None, 'set data using [Src, Rx]'
        assert isinstance(value, np.ndarray), 'value must by ndarray'
        assert value.size == rx.nD, (
            "value must have the same number of data as the source."
        )
        assert arr_name in ['dobs', 'standard_deviation', 'noise_floor'], (
            "has to be one of the settable array's: dobs, standard_deviation" +
            " or noise_floor")
        # Get the inds
        if len(self._data_dict) == 0:
            self._create_data_dict({'value': self.survey})
        inds = self._data_dict[src][rx]
        # Get the array
        arr = getattr(self, arr_name, None)
        if arr is None:
            arr = np.nan * np.ones(self.survey.nD)
        elif 'dobs' == arr_name:
            if not np.all(np.isnan(arr[inds])):
                raise Exception(
                    "Observed data cannot be overwritten. Create a new Data "
                    "object or a SyntheticData object instead"
                )
        arr[inds] = mkvc(value)
        setattr(self, arr_name, arr)

    def _get_data_properties(self, key, arr_name='dobs'):
        """
        Function to get dobs, standard_deviation or nosie_floor via
        [src, rx] pair
        """

        src, rx = self._ensureCorrectKey(key)
        arr = getattr(self, arr_name, None)
        # Get the inds
        if len(self._data_dict) == 0:
            self._create_data_dict({'value': self.survey})
        if rx is not None:
            if rx not in self._data_dict[src]:
                raise Exception('Data for receiver has not yet been set.')
            return arr[self._data_dict[src][rx]]

        return np.concatenate([
            arr[self._data_dict[src][rx]] for rx in src.rxList
        ])

    def __setitem__(self, key, value):
        self._set_data_properties(key, value)

    def __getitem__(self, key):
        return self._get_data_properties(key)

    @property
    def std(self):
        warnings.warn(
            "std has been depreciated in favor of standard_deviation. Please "
            "update your code to use 'standard_deviation'", DeprecationWarning
        )
        return self.standard_deviation

    @std.setter
    def std(self, value):
        warnings.warn(
            "std has been depreciated in favor of standard_deviation. Please "
            "update your code to use 'standard_deviation'", DeprecationWarning
        )
        self.standard_deviation = value

    @property
    def eps(self):
        warnings.warn(
            "eps has been depreciated in favor of noise_floor. Please "
            "update your code to use 'noise_floor'", DeprecationWarning
        )
        return self.noise_floor

    @eps.setter
    def eps(self, value):
        warnings.warn(
            "eps has been depreciated in favor of noise_floor. Please "
            "update your code to use 'noise_floor'", DeprecationWarning
        )
        self.noise_floor = value


class SyntheticData(Data):
    dclean = properties.Array(
        "observed data",
        shape=('*',),
        required=True
    )

    def __init__(self, **kwargs):
        super(SyntheticData, self).__init__(**kwargs)

    def __setitem__(self, key, value):
        src, rx = self._ensureCorrectKey(key)
        assert rx is not None, 'set data using [Src, Rx]'
        assert isinstance(value, np.ndarray), 'value must by ndarray'
        assert value.size == rx.nD, (
            "value must have the same number of data as the source."
        )
        inds = self._data_dict[src][rx]
        if getattr(self, 'dobs', None) is None:
            self.dobs = np.nan * np.ones(self.survey.nD)
        self.dobs[inds] = mkvc(value)
