""" Module RxNSEM.py

Receivers for the NSEM problem

"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from scipy.constants import mu_0
import numpy as np

import properties

from ..FDEM.RxFDEM import BaseFDEMRx
from discretize import BaseMesh
from .SrcNSEM import BaseNSEMSrc
from .FieldsNSEM import BaseNSEMFields
from ...Survey import RxLocationArray
from ...Utils import sdiag
from SimPEG import mkvc


#NOTE: has to inheret from BaseFDEMRx in order to be compatible
# with Src, since src.rxList is a list of BaseFDEMRx related objects
class BaseRxNSEM_Point(BaseFDEMRx):
    """
    Natural source receiver base class.

    Assumes that the data locations are xyz coordinates.

    :param numpy.ndarray locs: receiver locations (ie. :code:`np.r_[x,y,z]`)
    :param string orientation: receiver orientation 'x', 'y' or 'z'
    :param string component: real or imaginary component 'real' or 'imag'
    """

    # TODO: eventually, this should be a Vector3 and we can allow arbitraty
    # orientations
    orientation = properties.StringChoice(
        "Tensor orientation of the receiver 'xx', 'xy'," +
        "'yx', 'yy','zx', 'zy' ",
        choices=['xx', 'xy', 'yx', 'yy', 'zx', 'zy'],
        required=True
    )

    component = properties.StringChoice(
        "'real' or 'imag' component of the field to be measured",
        choices={
            'real': ['re', 'in-phase', 'inphase'],
            'imag': ['im', 'quadrature', 'quad', 'out-of-phase']
        },
        required=True
    )

    # Hidden properties to make projections less verbose
    _mesh = properties.Instance(
        'SimPEG mesh object',
        BaseMesh,
        default=None)

    _src = properties.Instance(
        'NSEM source',
        BaseNSEMSrc,
        default=None)

    _f = properties.Instance(
        'NSEM fields',
        BaseNSEMFields,
        default=None)


    def __init__(self, **kwargs):
        super(BaseRxNSEM_Point, self).__init__(**kwargs)

    def _loc_numerator(self):
        if self.locs.ndim == 3:
            loc = self.locs[:, :, 0]
        else:
            loc = self.locs
        return loc

    def _loc_denominator(self):
        if self.locs.ndim == 3:
            loc = self.locs[:, :, 1]
        else:
            loc = self.locs
        return loc

    # Location projection
    @property
    def Pex(self):
        if getattr(self, '_Pex', None) is None:
            self._Pex = self._mesh.getInterpolationMat(
                self._loc_numerator(), 'Ex')
        return self._Pex

    @property
    def Pey(self):
        if getattr(self, '_Pey', None) is None:
            self._Pey = self._mesh.getInterpolationMat(
                self._loc_numerator(), 'Ey')
        return self._Pey

    @property
    def Pbx(self):
        if getattr(self, '_Pbx', None) is None:
            self._Pbx = self._mesh.getInterpolationMat(
                self._loc_denominator(), 'Fx')
        return self._Pbx

    @property
    def Pby(self):
        if getattr(self, '_Pby', None) is None:
            self._Pby = self._mesh.getInterpolationMat(
                self._loc_denominator(), 'Fy')
        return self._Pby

    @property
    def Pbz(self):
        if getattr(self, '_Pbz', None) is None:
            self._Pbz = self._mesh.getInterpolationMat(
                self._loc_numerator(), 'Fz')
        return self._Pbz

    # Utility for convienece
    def _sDiag(self, t):
        return sdiag(mkvc(t, 2))

    # Get the components of the fields
    # px: x-polaration and py: y-polaration.
    @property
    def _ex_px(self):
        return self.Pex * self._f[self._src, 'e_px']

    @property
    def _ey_px(self):
        return self.Pey * self._f[self._src, 'e_px']

    @property
    def _ex_py(self):
        return self.Pex * self._f[self._src, 'e_py']

    @property
    def _ey_py(self):
        return self.Pey * self._f[self._src, 'e_py']

    @property
    def _hx_px(self):
        return self.Pbx * self._f[self._src, 'b_px'] / mu_0

    @property
    def _hy_px(self):
        return self.Pby * self._f[self._src, 'b_px'] / mu_0

    @property
    def _hz_px(self):
        return self.Pbz * self._f[self._src, 'b_px'] / mu_0

    @property
    def _hx_py(self):
        return self.Pbx * self._f[self._src, 'b_py'] / mu_0

    @property
    def _hy_py(self):
        return self.Pby * self._f[self._src, 'b_py'] / mu_0

    @property
    def _hz_py(self):
        return self.Pbz * self._f[self._src, 'b_py'] / mu_0
    # Get the derivatives

    def _ex_px_u(self, vec):
        return self.Pex * self._f._e_pxDeriv_u(self._src, vec)

    def _ey_px_u(self, vec):
        return self.Pey * self._f._e_pxDeriv_u(self._src, vec)

    def _ex_py_u(self, vec):
        return self.Pex * self._f._e_pyDeriv_u(self._src, vec)

    def _ey_py_u(self, vec):
        return self.Pey * self._f._e_pyDeriv_u(self._src, vec)

    def _hx_px_u(self, vec):
        return self.Pbx * self._f._b_pxDeriv_u(self._src, vec) / mu_0

    def _hy_px_u(self, vec):
        return self.Pby * self._f._b_pxDeriv_u(self._src, vec) / mu_0

    def _hz_px_u(self, vec):
        return self.Pbz * self._f._b_pxDeriv_u(self._src, vec) / mu_0

    def _hx_py_u(self, vec):
        return self.Pbx * self._f._b_pyDeriv_u(self._src, vec) / mu_0

    def _hy_py_u(self, vec):
        return self.Pby * self._f._b_pyDeriv_u(self._src, vec) / mu_0

    def _hz_py_u(self, vec):
        return self.Pbz * self._f._b_pyDeriv_u(self._src, vec) / mu_0
    # Define the components of the derivative

    @property
    def _Hd(self):
        return sdiag(1. / (
            sdiag(self._hx_px) * self._hy_py -
            sdiag(self._hx_py) * self._hy_px
        ))

    def _Hd_uV(self, v):
        return (
            sdiag(self._hy_py) * self._hx_px_u(v) +
            sdiag(self._hx_px) * self._hy_py_u(v) -
            sdiag(self._hx_py) * self._hy_px_u(v) -
            sdiag(self._hy_px) * self._hx_py_u(v)
        )

    # Adjoint
    @property
    def _aex_px(self):
        return mkvc(mkvc(self._f[self._src, 'e_px'], 2).T * self.Pex.T)

    @property
    def _aey_px(self):
        return mkvc(mkvc(self._f[self._src, 'e_px'], 2).T * self.Pey.T)

    @property
    def _aex_py(self):
        return mkvc(mkvc(self._f[self._src, 'e_py'], 2).T * self.Pex.T)

    @property
    def _aey_py(self):
        return mkvc(mkvc(self._f[self._src, 'e_py'], 2).T * self.Pey.T)

    @property
    def _ahx_px(self):
        return mkvc(mkvc(self._f[self._src, 'b_px'], 2).T / mu_0 * self.Pbx.T)

    @property
    def _ahy_px(self):
        return mkvc(mkvc(self._f[self._src, 'b_px'], 2).T / mu_0 * self.Pby.T)

    @property
    def _ahz_px(self):
        return mkvc(mkvc(self._f[self._src, 'b_px'], 2).T / mu_0 * self.Pbz.T)

    @property
    def _ahx_py(self):
        return mkvc(mkvc(self._f[self._src, 'b_py'], 2).T / mu_0 * self.Pbx.T)

    @property
    def _ahy_py(self):
        return mkvc(mkvc(self._f[self._src, 'b_py'], 2).T / mu_0 * self.Pby.T)

    @property
    def _ahz_py(self):
        return mkvc(mkvc(self._f[self._src, 'b_py'], 2).T / mu_0 * self.Pbz.T)

    # NOTE: need to add a .T at the end for the output to be (nU,)
    def _aex_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._e_pxDeriv_u(
            self._src, self.Pex.T * mkvc(vec,), adjoint=True)

    def _aey_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._e_pxDeriv_u(
            self._src, self.Pey.T * mkvc(vec,), adjoint=True)

    def _aex_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._e_pyDeriv_u(
            self._src, self.Pex.T * mkvc(vec,), adjoint=True)

    def _aey_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._e_pyDeriv_u(
            self._src, self.Pey.T * mkvc(vec,), adjoint=True)

    def _ahx_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pxDeriv_u(
            self._src, self.Pbx.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahy_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pxDeriv_u(
            self._src, self.Pby.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahz_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pxDeriv_u(
            self._src, self.Pbz.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahx_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pyDeriv_u(
            self._src, self.Pbx.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahy_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pyDeriv_u(
            self._src, self.Pby.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahz_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pyDeriv_u(
            self._src, self.Pbz.T * mkvc(vec,), adjoint=True) / mu_0

    # Define the components of the derivative
    @property
    def _aHd(self):
        return sdiag(1. / (
            sdiag(self._ahx_px) * self._ahy_py -
            sdiag(self._ahx_py) * self._ahy_px
        ))

    def _aHd_uV(self, x):
        return (
            self._ahx_px_u(sdiag(self._ahy_py) * x) +
            self._ahx_px_u(sdiag(self._ahy_py) * x) -
            self._ahy_px_u(sdiag(self._ahx_py) * x) -
            self._ahx_py_u(sdiag(self._ahy_px) * x)
        )

    def eval(self, src, mesh, f, return_complex=False):
        """
        Function to evaluate datum for this receiver
        """
        raise NotImplementedError(
            'SimPEG.EM.NSEM receiver has to have an eval method')

    def evalDeriv(self, src, mesh, f, v, adjoint=False):
        """
        Function to evaluate datum for this receiver
        """
        raise NotImplementedError(
            'SimPEG.EM.NSEM receiver has to have an evalDeriv method')


class Point_impedance1D(BaseFDEMRx):
    """
    Natural source 1D impedance receiver class

    :param string component: real or imaginary component 'real' or 'imag'
    """

    orientation = properties.GettableProperty(
        "The tensor orientation of the receiver. Default as 'yx'",
        default='yx'
    )

    component = properties.StringChoice(
        "'real' or 'imag' component of the field to be measured",
        choices={
            'real': ['re', 'in-phase', 'inphase'],
            'imag': ['im', 'quadrature', 'quad', 'out-of-phase']
        },
        required=True
    )

    # Hidden properties to make projections less verbose
    _mesh = properties.Instance(
        'SimPEG mesh object',
        BaseMesh,
        default=None)

    _src = properties.Instance(
        'NSEM source',
        BaseNSEMSrc,
        default=None)

    _f = properties.Instance(
        'NSEM fields',
        BaseNSEMFields,
        default=None)

    def __init__(self, **kwargs):
        super(Point_impedance1D, self).__init__(**kwargs)

    @property
    def Pex(self):
        if getattr(self, '_Pex', None) is None:
            self._Pex = self._mesh.getInterpolationMat(self.locs[:, -1], 'Fx')
        return self._Pex

    @property
    def Pbx(self):
        if getattr(self, '_Pbx', None) is None:
            self._Pbx = self._mesh.getInterpolationMat(self.locs[:, -1], 'Ex')
        return self._Pbx

    @property
    def _ex(self):
        return self.Pex * mkvc(self._f[self._src, 'e_1d'], 2)

    @property
    def _hx(self):
        return self.Pbx * mkvc(self._f[self._src, 'b_1d'], 2) / mu_0

    def _ex_u(self, v):
        return self.Pex * self._f._eDeriv_u(self._src, v)

    def _hx_u(self, v):
        return self.Pbx * self._f._bDeriv_u(self._src, v) / mu_0

    def _aex_u(self, v):
        return self._f._eDeriv_u(self._src, self.Pex.T * v, adjoint=True)

    def _ahx_u(self, v):
        return self._f._bDeriv_u(
            self._src, self.Pbx.T * v, adjoint=True) / mu_0

    @property
    def _Hd(self):
        return sdiag(1./self._hx)

    def eval(self, src, mesh, f, return_complex=False):
        '''
        Project the fields to natural source data.

        :param SimPEG.EM.NSEM.SrcNSEM src: NSEM source
        :param discretize.TensorMesh mesh: Mesh defining the topology of the problem
        :param SimPEG.EM.NSEM.FieldsNSEM f: NSEM fields object of the source
        :param bool (optional) return_complex: Flag for return the complex evaluation
        :rtype: numpy.array
        :return: Evaluated data for the receiver
        '''
        # NOTE: Maybe set this as a property
        self._src = src
        self._mesh = mesh
        self._f = f

        rx_eval_complex = -self._Hd * self._ex
        # Return the full impedance
        if return_complex:
            return rx_eval_complex
        return getattr(rx_eval_complex, self.component)

    def evalDeriv(self, src, mesh, f, v, adjoint=False):
        """method evalDeriv

        The derivative of the projection wrt u

        :param SimPEG.EM.NSEM.SrcNSEM src: NSEM source
        :param discretize.TensorMesh mesh: Mesh defining the topology of the problem
        :param SimPEG.EM.NSEM.FieldsNSEM f: NSEM fields object of the source
        :param numpy.ndarray v: vector of size (nU,) (adjoint=False) and size (nD,) (adjoint=True)
        :rtype: numpy.array
        :return: Calculated derivative (nD,) (adjoint=False) and (nP,2) (adjoint=True) for both polarizations
        """
        self._src = src
        self._mesh = mesh
        self._f = f

        if adjoint:
            Z1d = self.eval(src, mesh, f, True)

            def aZ_N_uV(x):
                return -self._aex_u(x)

            def aZ_D_uV(x):
                return self._ahx_u(x)
            rx_deriv = aZ_N_uV(
                self._Hd.T * v) - aZ_D_uV(sdiag(Z1d).T * self._Hd.T * v)
            if self.component == 'imag':
                rx_deriv_component = 1j * rx_deriv
            elif self.component == 'real':
                rx_deriv_component = rx_deriv.astype(complex)
        else:
            Z1d = self.eval(src, mesh, f, True)
            Z_N_uV = -self._ex_u(v)
            Z_D_uV = self._hx_u(v)
            # Evaluate
            rx_deriv = self._Hd * (Z_N_uV - sdiag(Z1d) * Z_D_uV)
            rx_deriv_component = np.array(getattr(rx_deriv, self.component))
        return rx_deriv_component


class Point_impedance3D(BaseRxNSEM_Point):
    """
    Natural source 3D impedance receiver class

    :param numpy.ndarray locs: receiver locations (ie. :code:`np.r_[x,y,z]`)
    :param string orientation: receiver orientation 'xx', 'xy', 'yx' or 'yy'
    :param string component: real or imaginary component 'real' or 'imag'
    """

    def __init__(self, **kwargs):

        super(Point_impedance3D, self).__init__(**kwargs)

    def eval(self, src, mesh, f, return_complex=False):
        '''
        Project the fields to natural source data.

        :param SrcNSEM src: The source of the fields to project
        :param discretize.TensorMesh mesh: topological mesh corresponding to the fields
        :param FieldsNSEM f: Natural source fields object to project
        :rtype: numpy.array
        :return: component of the impedance evaluation
        '''
        # NOTE: Maybe set this as a property
        self._src = src
        self._mesh = mesh
        self._f = f

        if 'xx' in self.orientation:
            Zij = (self._ex_px * self._hy_py - self._ex_py * self._hy_px)
        elif 'xy' in self.orientation:
            Zij = (-self._ex_px * self._hx_py + self._ex_py * self._hx_px)
        elif 'yx' in self.orientation:
            Zij = (self._ey_px * self._hy_py - self._ey_py * self._hy_px)
        elif 'yy' in self.orientation:
            Zij = (-self._ey_px * self._hx_py + self._ey_py * self._hx_px)
        # Calculate the complex value
        rx_eval_complex = self._Hd * Zij

        # Return the full impedance
        if return_complex:
            return rx_eval_complex
        return getattr(rx_eval_complex, self.component)

    def evalDeriv(self, src, mesh, f, v, adjoint=False):
        """
        The derivative of the projection wrt u

        :param SimPEG.EM.NSEM.SrcNSEM src: NSEM source
        :param discretize.TensorMesh mesh: Mesh defining the topology of the problem
        :param SimPEG.EM.NSEM.FieldsNSEM f: NSEM fields object of the source
        :param numpy.ndarray v: vector of size (nU,) (adjoint=False) and size (nD,) (adjoint=True)
        :rtype: numpy.array
        :return: Calculated derivative (nD,) (adjoint=False) and (nP,2) (adjoint=True) for both polarizations
        """
        self._src = src
        self._mesh = mesh
        self._f = f

        if adjoint:
            if 'xx' in self.orientation:
                Zij = sdiag(self._aHd * (
                    sdiag(self._ahy_py)*self._aex_px -
                    sdiag(self._ahy_px)*self._aex_py
                ))

                def ZijN_uV(x):
                    return (
                        self._aex_px_u(sdiag(self._ahy_py) * x) +
                        self._ahy_py_u(sdiag(self._aex_px) * x) -
                        self._ahy_px_u(sdiag(self._aex_py) * x) -
                        self._aex_py_u(sdiag(self._ahy_px) * x)
                    )
            elif 'xy' in self.orientation:
                Zij = sdiag(self._aHd * (
                    -sdiag(self._ahx_py) * self._aex_px +
                    sdiag(self._ahx_px) * self._aex_py
                ))

                def ZijN_uV(x):
                    return (
                        -self._aex_px_u(sdiag(self._ahx_py) * x) -
                        self._ahx_py_u(sdiag(self._aex_px) * x) +
                        self._ahx_px_u(sdiag(self._aex_py) * x) +
                        self._aex_py_u(sdiag(self._ahx_px) * x)
                    )
            elif 'yx' in self.orientation:
                Zij = sdiag(self._aHd * (
                    sdiag(self._ahy_py) * self._aey_px -
                    sdiag(self._ahy_px) * self._aey_py
                ))

                def ZijN_uV(x):
                    return (
                        self._aey_px_u(sdiag(self._ahy_py) * x) +
                        self._ahy_py_u(sdiag(self._aey_px) * x) -
                        self._ahy_px_u(sdiag(self._aey_py) * x) -
                        self._aey_py_u(sdiag(self._ahy_px) * x)
                    )
            elif 'yy' in self.orientation:
                Zij = sdiag(self._aHd * (
                    -sdiag(self._ahx_py) * self._aey_px +
                    sdiag(self._ahx_px) * self._aey_py))

                def ZijN_uV(x):
                    return (
                        -self._aey_px_u(sdiag(self._ahx_py) * x) -
                        self._ahx_py_u(sdiag(self._aey_px) * x) +
                        self._ahx_px_u(sdiag(self._aey_py) * x) +
                        self._aey_py_u(sdiag(self._ahx_px) * x)
                    )

            # Calculate the complex derivative
            rx_deriv_real = ZijN_uV(
                self._aHd * v) - self._aHd_uV(Zij.T * self._aHd * v)
            # NOTE: Need to reshape the output to go from 2*nU array to a (nU,2) matrix for each polarization
            # rx_deriv_real = np.hstack((mkvc(rx_deriv_real[:len(rx_deriv_real)/2],2),mkvc(rx_deriv_real[len(rx_deriv_real)/2::],2)))
            rx_deriv_real = rx_deriv_real.reshape((2, self._mesh.nE)).T
            # Extract the data
            if self.component == 'imag':
                rx_deriv_component = 1j * rx_deriv_real
            elif self.component == 'real':
                rx_deriv_component = rx_deriv_real.astype(complex)
        else:
            if 'xx' in self.orientation:
                ZijN_uV = (
                    sdiag(self._hy_py) * self._ex_px_u(v) +
                    sdiag(self._ex_px) * self._hy_py_u(v) -
                    sdiag(self._ex_py) * self._hy_px_u(v) -
                    sdiag(self._hy_px) * self._ex_py_u(v)
                )
            elif 'xy' in self.orientation:
                ZijN_uV = (
                    -sdiag(self._hx_py) * self._ex_px_u(v) -
                    sdiag(self._ex_px) * self._hx_py_u(v) +
                    sdiag(self._ex_py) * self._hx_px_u(v) +
                    sdiag(self._hx_px) * self._ex_py_u(v)
                )
            elif 'yx' in self.orientation:
                ZijN_uV = (
                    sdiag(self._hy_py) * self._ey_px_u(v) +
                    sdiag(self._ey_px) * self._hy_py_u(v) -
                    sdiag(self._ey_py) * self._hy_px_u(v) -
                    sdiag(self._hy_px) * self._ey_py_u(v)
                )
            elif 'yy' in self.orientation:
                ZijN_uV = (
                    -sdiag(self._hx_py) * self._ey_px_u(v) -
                    sdiag(self._ey_px) * self._hx_py_u(v) +
                    sdiag(self._ey_py) * self._hx_px_u(v) +
                    sdiag(self._hx_px) * self._ey_py_u(v)
                )

            Zij = self.eval(
                self._src, self._mesh, self._f, True)
            # Calculate the complex derivative
            rx_deriv_real = self._Hd * (ZijN_uV - sdiag(Zij) * self._Hd_uV(v))
            rx_deriv_component = np.array(
                getattr(rx_deriv_real, self.component))

        return rx_deriv_component


class Point_tipper3D(BaseRxNSEM_Point):
    """
    Natural source 3D tipper receiver base class

    :param numpy.ndarray locs: receiver locations (ie. :code:`np.r_[x,y,z]`)
    :param string orientation: receiver orientation 'x', 'y' or 'z'
    :param string component: real or imaginary component 'real' or 'imag'
    """

    def __init__(self, **kwargs):

        super(Point_tipper3D, self).__init__(**kwargs)

    def eval(self, src, mesh, f, return_complex=False):
        '''
        Project the fields to natural source data.

        :param SrcNSEM src: The source of the fields to project
        :param discretize.TensorMesh mesh: Mesh defining the topology of the problem
        :param FieldsNSEM f: Natural source fields object to project
        :rtype: numpy.array
        :return: Evaluated component of the impedance data
        '''
        # NOTE: Maybe set this as a property
        self._src = src
        self._mesh = mesh
        self._f = f

        if 'zx' in self.orientation:
            Tij = (- self._hy_px * self._hz_py + self._hy_py * self._hz_px)
        if 'zy' in self.orientation:
            Tij = (self._hx_px * self._hz_py - self._hx_py * self._hz_px)
        rx_eval_complex = self._Hd * Tij

        # Return the full impedance
        if return_complex:
            return rx_eval_complex
        return getattr(rx_eval_complex, self.component)

    def evalDeriv(self, src, mesh, f, v, adjoint=False):
        """
        The derivative of the projection wrt u

        :param SimPEG.EM.NSEM.SrcNSEM src: NSEM source
        :param discretize.TensorMesh mesh: Mesh defining the topology of the problem
        :param SimPEG.EM.NSEM.FieldsNSEM f: NSEM fields object of the source
        :param numpy.ndarray v: Random vector of size
        :rtype: numpy.array
        :return: Calculated derivative (nD,) (adjoint=False) and (nP,2) (adjoint=True)
            for both polarizations
        """
        self._src = src
        self._mesh = mesh
        self._f = f

        if adjoint:
            if 'zx' in self.orientation:
                Tij = sdiag(self._aHd * (
                    -sdiag(self._ahz_py) * self._ahy_px +
                    sdiag(self._ahz_px) * self._ahy_py)
                )

                def TijN_uV(x):
                    return (
                        -self._ahz_py_u(sdiag(self._ahy_px) * x) -
                        self._ahy_px_u(sdiag(self._ahz_py) * x) +
                        self._ahy_py_u(sdiag(self._ahz_px) * x) +
                        self._ahz_px_u(sdiag(self._ahy_py) * x)
                    )
            elif 'zy' in self.orientation:
                Tij = sdiag(self._aHd * (
                    sdiag(self._ahz_py) * self._ahx_px -
                    sdiag(self._ahz_px) * self._ahx_py)
                )

                def TijN_uV(x):
                    return (
                        self._ahx_px_u(sdiag(self._ahz_py) * x) +
                        self._ahz_py_u(sdiag(self._ahx_px) * x) -
                        self._ahx_py_u(sdiag(self._ahz_px) * x) -
                        self._ahz_px_u(sdiag(self._ahx_py) * x)
                    )

            # Calculate the complex derivative
            rx_deriv_real = (
                TijN_uV(self._aHd * v) -
                self._aHd_uV(Tij.T * self._aHd * v)
            )
            # NOTE: Need to reshape the output to go from 2*nU array to a (nU,2) matrix for each polarization
            # rx_deriv_real = np.hstack((mkvc(rx_deriv_real[:len(rx_deriv_real)/2],2),mkvc(rx_deriv_real[len(rx_deriv_real)/2::],2)))
            rx_deriv_real = rx_deriv_real.reshape((2, self._mesh.nE)).T
            # Extract the data
            if self.component == 'imag':
                rx_deriv_component = 1j * rx_deriv_real
            elif self.component == 'real':
                rx_deriv_component = rx_deriv_real.astype(complex)
        else:
            if 'zx' in self.orientation:
                TijN_uV = (
                    -sdiag(self._hy_px) * self._hz_py_u(v) -
                    sdiag(self._hz_py) * self._hy_px_u(v) +
                    sdiag(self._hy_py) * self._hz_px_u(v) +
                    sdiag(self._hz_px) * self._hy_py_u(v)
                )
            elif 'zy' in self.orientation:
                TijN_uV = (
                    sdiag(self._hz_py) * self._hx_px_u(v) +
                    sdiag(self._hx_px) * self._hz_py_u(v) -
                    sdiag(self._hx_py) * self._hz_px_u(v) -
                    sdiag(self._hz_px) * self._hx_py_u(v)
                )
            Tij = self.eval(src, mesh, f, True)
            # Calculate the complex derivative
            rx_deriv_complex = (
                self._Hd * (TijN_uV - sdiag(Tij) * self._Hd_uV(v))
            )
            rx_deriv_component = np.array(
                getattr(rx_deriv_complex, self.component)
            )

        return rx_deriv_component


class Point_horizontalmagvar3D(BaseRxNSEM_Point):
    """
    Natural source 3D horizontal magnetic tensor receiver base class
    :param numpy.ndarray locs: receiver locations (ie. :code:`np.r_[x,y,z]`)
    :param string orientation: receiver orientation 'xx', 'xy','yx' or 'yy'
    :param string component: real or imaginary component 'real' or 'imag'
    """
    # location
    locs = RxLocationArray(
        "Locations of the receivers (nRx x nDim x 2)",
        shape=("*", "*", "*"),
        required=True
    )

    def __init__(self, **kwargs):

        super(Point_horizontalmagvar3D, self).__init__(**kwargs)

    @property
    def Pbx_num(self):
        if getattr(self, '_Pbx_num', None) is None:
            self._Pbx_num = self._mesh.getInterpolationMat(
                self._loc_numerator(), 'Fx')
        return self._Pbx_num

    @property
    def Pby_num(self):
        if getattr(self, '_Pby_num', None) is None:
            self._Pby_num = self._mesh.getInterpolationMat(
                self._loc_numerator(), 'Fy')
        return self._Pby_num


    @property
    def _hx_num_px(self):
        return self.Pbx_num * self._f[self._src, 'b_px'] / mu_0

    @property
    def _hy_num_px(self):
        return self.Pby_num * self._f[self._src, 'b_px'] / mu_0

    @property
    def _hx_num_py(self):
        return self.Pbx_num * self._f[self._src, 'b_py'] / mu_0

    @property
    def _hy_num_py(self):
        return self.Pby_num * self._f[self._src, 'b_py'] / mu_0

    # Get the derivatives

    def _hx_num_px_u(self, vec):
        return self.Pbx_num * self._f._b_pxDeriv_u(self._src, vec) / mu_0

    def _hy_num_px_u(self, vec):
        return self.Pby_num * self._f._b_pxDeriv_u(self._src, vec) / mu_0

    def _hx_num_py_u(self, vec):
        return self.Pbx_num * self._f._b_pyDeriv_u(self._src, vec) / mu_0

    def _hy_num_py_u(self, vec):
        return self.Pby_num * self._f._b_pyDeriv_u(self._src, vec) / mu_0

    # Define the components of the derivative
    # Overwrite the base
    @property
    def _Hd(self):
        return self._sDiag(1. / (
            self._sDiag(self._hx_px) * self._hy_py -
            self._sDiag(self._hx_py) * self._hy_px
        ))

    def _Hd_uV(self, v):
        return (
            self._sDiag(self._hy_py) * self._hx_px_u(v) +
            self._sDiag(self._hx_px) * self._hy_py_u(v) -
            self._sDiag(self._hx_py) * self._hy_px_u(v) -
            self._sDiag(self._hy_px) * self._hx_py_u(v)
        )

    @property
    def _ahx_num_px(self):
        return mkvc(
            mkvc(self._f[self._src, 'b_px'], 2).T / mu_0 * self.Pbx_num.T)

    @property
    def _ahy_num_px(self):
        return mkvc(
            mkvc(self._f[self._src, 'b_px'], 2).T / mu_0 * self.Pby_num.T)

    @property
    def _ahx_num_py(self):
        return mkvc(
            mkvc(self._f[self._src, 'b_py'], 2).T / mu_0 * self.Pbx_num.T)

    @property
    def _ahy_num_py(self):
        return mkvc(
            mkvc(self._f[self._src, 'b_py'], 2).T / mu_0 * self.Pby_num.T)

    # NOTE: need to add a .T at the end for the output to be (nU,)
    def _ahx_num_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pxDeriv_u(
            self._src, self.Pbx_num.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahy_num_px_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pxDeriv_u(
            self._src, self.Pby_num.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahx_num_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pyDeriv_u(
            self._src, self.Pbx_num.T * mkvc(vec,), adjoint=True) / mu_0

    def _ahy_num_py_u(self, vec):
        """
        """
        # vec is (nD,) and returns a (nU,)
        return self._f._b_pyDeriv_u(
            self._src, self.Pby_num.T * mkvc(vec,), adjoint=True) / mu_0

    # Define the components of the derivative
    @property
    def _aHd(self):
        return self._sDiag(1. / (
            self._sDiag(self._ahx_px) * self._ahy_py -
            self._sDiag(self._ahx_py) * self._ahy_px
        ))

    def _aHd_uV(self, x):
        return (
            self._ahx_px_u(self._sDiag(self._ahy_py) * x) +
            self._ahx_px_u(self._sDiag(self._ahy_py) * x) -
            self._ahy_px_u(self._sDiag(self._ahx_py) * x) -
            self._ahx_py_u(self._sDiag(self._ahy_px) * x)
        )

    def eval(self, src, mesh, f, return_complex=False):
        '''
        Project the fields to natural source data.
        Uses Schmucker convention,
        :param SrcNSEM src: The source of the fields to project
        :param SimPEG.Mesh.TensorMesh mesh: Mesh defining the topology of the problem
        :param FieldsNSEM f: Natural source fields object to project
        :rtype: numpy.array
        :return: Evaluated component of the horizontal magnetic transfer data
        '''

        # NOTE: Maybe set this as a property
        self._src = src
        self._mesh = mesh
        self._f = f

        if 'xx' in self.orientation:
            Mij = (
                self._hx_num_px * self._hy_py -
                self._hx_num_py * self._hy_px)
            schmucker_corr = 1.
        elif 'xy' in self.orientation:
            Mij = (
                -self._hx_num_px * self._hx_py +
                self._hx_num_py * self._hx_px)
            schmucker_corr = 0.
        elif 'yx' in self.orientation:
            Mij = (
                self._hy_num_px * self._hy_py -
                self._hy_num_py * self._hy_px)
            schmucker_corr = 0.
        elif 'yy' in self.orientation:
            Mij = (
                -self._hy_num_px * self._hx_py +
                self._hy_num_py * self._hx_px)
            schmucker_corr = 1.

        # Evaluate
        rx_eval_complex = (self._Hd * Mij) - schmucker_corr

        # Return the full impedance
        if return_complex:
            return rx_eval_complex
        return getattr(rx_eval_complex, self.component)

    def evalDeriv(self, src, mesh, f, v, adjoint=False):
        """
        The derivative of the projection wrt u
        :param SimPEG.EM.NSEM.SrcNSEM src: NSEM source
        :param SimPEG.Mesh.TensorMesh mesh: Mesh defining the topology of the problem
        :param SimPEG.EM.NSEM.FieldsNSEM f: NSEM fields object of the source
        :param numpy.ndarray v: A vector of size
        :rtype: numpy.array
        :return: Calculated derivative (nD,) (adjoint=False) and (nP,2) (adjoint=True)
            for both polarizations
        """
        self._src = src
        self._mesh = mesh
        self._f = f

        if adjoint:
            if 'xx' in self.orientation:
                Mij = self._sDiag(self._aHd * (
                    self._sDiag(self._ahy_py) * self._ahx_num_px -
                    self._sDiag(self._ahy_px) * self._ahx_num_py
                ))

                def MijN_uV(x):
                    return (
                        self._ahx_num_px_u(self._sDiag(self._ahy_py) * x) +
                        self._ahy_py_u(self._sDiag(self._ahx_num_px) * x) -
                        self._ahy_px_u(self._sDiag(self._ahx_num_py) * x) -
                        self._ahx_num_py_u(self._sDiag(self._ahy_px) * x)
                    )
            elif 'xy' in self.orientation:
                Mij = self._sDiag(self._aHd * (
                    -self._sDiag(self._ahx_py) * self._ahx_num_px +
                    self._sDiag(self._ahx_px) * self._ahx_num_py
                ))

                def MijN_uV(x):
                    return (
                        -self._ahx_num_px_u(self._sDiag(self._ahx_py) * x) -
                        self._ahx_py_u(self._sDiag(self._ahx_num_px) * x) +
                        self._ahx_px_u(self._sDiag(self._ahx_num_py) * x) +
                        self._ahx_num_py_u(self._sDiag(self._ahx_px) * x)
                    )
            elif 'yx' in self.orientation:
                Mij = self._sDiag(self._aHd * (
                    self._sDiag(self._ahy_py) * self._ahy_num_px -
                    self._sDiag(self._ahy_px) * self._ahy_num_py
                ))

                def MijN_uV(x):
                    return (
                        self._ahy_num_px_u(self._sDiag(self._ahy_py) * x) +
                        self._ahy_py_u(self._sDiag(self._ahy_num_px) * x) -
                        self._ahy_px_u(self._sDiag(self._ahy_num_py) * x) -
                        self._ahy_num_py_u(self._sDiag(self._ahy_px) * x)
                    )
            elif 'yy' in self.orientation:
                Mij = self._sDiag(self._aHd * (
                    -self._sDiag(self._ahx_py) * self._ahy_num_px +
                    self._sDiag(self._ahx_px) * self._ahy_num_py))

                def MijN_uV(x):
                    return (
                        -self._ahy_num_px_u(self._sDiag(self._ahx_py) * x) -
                        self._ahx_py_u(self._sDiag(self._ahy_num_px) * x) +
                        self._ahx_px_u(self._sDiag(self._ahy_num_py) * x) +
                        self._ahy_num_py_u(self._sDiag(self._ahx_px) * x)
                    )

            # Calculate the complex derivative
            rx_deriv_real = (
                MijN_uV(self._aHd * v) -
                self._aHd_uV(Mij.T * self._aHd * v))
            # NOTE: Need to reshape the output to go from 2 * nU array to a (nU,2) matrix for each polarization
            # rx_deriv_real = np.hstack((mkvc(rx_deriv_real[:len(rx_deriv_real)/2],2),mkvc(rx_deriv_real[len(rx_deriv_real)/2::],2)))
            rx_deriv_real = rx_deriv_real.reshape((2, self._mesh.nE)).T
            # Extract the data
            if self.component == 'imag':
                rx_deriv_component = 1j * rx_deriv_real
            elif self.component == 'real':
                rx_deriv_component = rx_deriv_real.astype(complex)
        else:
            if 'xx' in self.orientation:
                MijN_uV = (
                    self._sDiag(self._hy_py) * self._hx_num_px_u(v) +
                    self._sDiag(self._hx_num_px) * self._hy_py_u(v) -
                    self._sDiag(self._hx_num_py) * self._hy_px_u(v) -
                    self._sDiag(self._hy_px) * self._hx_num_py_u(v)
                )
                schmucker_corr = 1.
            elif 'xy' in self.orientation:
                MijN_uV = (
                    -self._sDiag(self._hx_py) * self._hx_num_px_u(v) -
                    self._sDiag(self._hx_num_px) * self._hx_py_u(v) +
                    self._sDiag(self._hx_num_py) * self._hx_px_u(v) +
                    self._sDiag(self._hx_px) * self._hx_num_py_u(v)
                )
                schmucker_corr = 0.
            elif 'yx' in self.orientation:
                MijN_uV = (
                    self._sDiag(self._hy_py) * self._hy_num_px_u(v) +
                    self._sDiag(self._hy_num_px) * self._hy_py_u(v) -
                    self._sDiag(self._hy_num_py) * self._hy_px_u(v) -
                    self._sDiag(self._hy_px) * self._hy_num_py_u(v)
                )
                schmucker_corr = 0.
            elif 'yy' in self.orientation:
                MijN_uV = (
                    -self._sDiag(self._hx_py) * self._hy_num_px_u(v) -
                    self._sDiag(self._hy_num_px) * self._hx_py_u(v) +
                    self._sDiag(self._hy_num_py) * self._hx_px_u(v) +
                    self._sDiag(self._hx_px) * self._hy_num_py_u(v)
                )
                schmucker_corr = 1.

            Mij = self.eval(src, self._mesh, self._f, True) + schmucker_corr
            # Calculate the complex derivative
            rx_deriv_real = self._Hd * (
                MijN_uV - self._sDiag(Mij) * self._Hd_uV(v))
            rx_deriv_component = np.array(
                getattr(rx_deriv_real, self.component))

        return rx_deriv_component
