"""
Inspect the Gaussian decomposition of EBHIS and GASS
"""

"""
Functions
---------

inspect_spectra(data_table, model_table, nsamples) : Inspect a given, random
    number of spectra
"""

import tables
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import pylab as pl
import argparse

import healpy as hp

from specfitting import make_multi_gaussian_model

# convert channels to m/s
CRPIX3 = 471.921630003202
CDELT3 = 1288.23448620083

def chan2velo(channel):
    """
    Convert EBHIS channel number to LSR velocity in m/s
    """
    return (channel - CRPIX3) * CDELT3


def reconstruct_coldens(table):
    """
    Reconstruct a column density map of the full sky at nside=1024
    """
    npix = hp.nside2npix(2**10)
    hi_model = np.zeros(npix, dtype=np.float32)

    for row in table:
        hi_model[row['hpxindex']] += row['amplitude']

    # convert to cm**-2, 1.288 is EBHIS chanwidth
    to_coldens = 1.82e18 * 1.288

    return hi_model * to_coldens


def make_ncomp_map(table):
    """
    Create a map of the number of components, used to model the HI emission
    """
    npix = hp.nside2npix(2**10)
    ncomps = np.zeros(npix, dtype=int)

    for row in table:
        ncomps[row['hpxindex']] += 1

    return ncomps


def inspect_spectra(data_table, model_table, nsamples, x_model):
    """
    Inspect a given, random number of spectra
    """
    model_functions = make_multi_gaussian_model()
    f_model = model_functions[0]

    # draw random, unique hpxindices
    indices = np.unique(model_table.cols.hpxindex[:])
    sample_indices = np.random.choice(indices, size=nsamples, replace=False)

    spectra = []
    model_spectra = []
    for sample_index in sample_indices:
        # data
        spectra.append(np.squeeze(
            data_table.read_where("""HPXINDEX=={}""".format(sample_index))['DATA']))

        # model
        gauss_params = np.array([[row['amplitude'], row['center_kms'], row['width_kms']] for row in model_table.where("""hpxindex=={}""".format(sample_index))])
        model_spectra.append(CDELT3 * f_model(gauss_params.flatten(), x_model)[1])

    return spectra, model_spectra


def main():
    """
    Inspect the Gaussian decomposition of EBHIS and GASS
    """

    # evaluate parsed arguments
    argp = argparse.ArgumentParser(description=__doc__)

    argp.add_argument(
        '-g',
        '--gaussdec',
        help='location of the Gaussian decomposition',
        type=str)

    argp.add_argument(
        '-d',
        '--data',
        default='/users/dlenz/projects/ebhis2pytable/data/ebhis.h5',
        metavar='infile',
        help='Data pytable',
        type=str)

    argp.add_argument(
        '-n',
        '--nsamples',
        default=5,
        help='Number of random sightlines that are inspected',
        type=int)

    args = argp.parse_args()

    # load tables
    gdec_store = tables.open_file(args.gaussdec, mode="r", title="Gaussdec")
    gdec = gdec_store.root.gaussdec_ebhis

    ebhis_store = tables.open_file(
        args.data,
        mode="r")
    ebhis = ebhis_store.root.ebhis

    # inspect reconstruction
    # hi_model = reconstruct_coldens(table=gdec)
    # hp.mollview(hi_model, xsize=4000.)

    # inspect spectra
    x_data = chan2velo(np.arange(945))
    x_model = np.linspace(-500.e3, 500.e3, 1e4)

    spectra, model_spectra = inspect_spectra(
        data_table=ebhis,
        model_table=gdec,
        nsamples=10,
        x_model=x_model)

    shift = 0
    for i, (spectrum, model_spectrum) in enumerate(zip(spectra, model_spectra)):
        pl.plot(x_data, spectrum + shift)
        pl.plot(x_model, model_spectrum + shift)
        shift += np.nanmax(spectrum) 

    pl.show()


if __name__ == '__main__':
    main()







