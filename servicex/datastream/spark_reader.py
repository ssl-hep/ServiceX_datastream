# Copyright (c) 2019, IRIS-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import awkward.arrow
import numpy as np
import pyarrow as pa
import uproot_methods
from fnal_column_analysis_tools.analysis_objects import JaggedCandidateArray
from pyspark.sql import SparkSession


#functions to quickly cash useful quantities
# from servicex.datastream.servicex_candidate_array import \
#     ServiceXCandidateMethods


def _fast_pt(p4):
    """ quick pt calculation for caching """
    return np.hypot(p4.x,p4.y)

def _fast_eta(p4):
    """ quick eta calculation for caching """
    px = p4.x
    py = p4.y
    pz = p4.z
    pT = np.sqrt(px*px + py*py)
    return np.arcsinh(pz/pT)

def _fast_phi(p4):
    """ quick phi calculation for caching """
    return np.arctan2(p4.y,p4.x)

def _fast_mass(p4):
    """ quick mass calculation for caching """
    px = p4.x
    py = p4.y
    pz = p4.z
    en = p4.t
    p3mag2 = (px*px + py*py + pz*pz)
    return np.sqrt(np.abs(en*en - p3mag2))

def candidatesfromoffsets(offsets, **kwargs):
    """
        cands = JaggedCandidateArray.candidatesfromoffsets(offsets=offsets,
                                                           pt=column1,
                                                           eta=column2,
                                                           phi=column3,
                                                           mass=column4,
                                                           ...)
    """
    items = kwargs
    argkeys = items.keys()
    p4 = None
    fast_pt = None
    fast_eta = None
    fast_phi = None
    fast_mass = None
    if 'p4' in argkeys:
        p4 = items['p4']
        if not isinstance(p4, uproot_methods.TLorentzVectorArray):
            p4 = uproot_methods.TLorentzVectorArray.from_cartesian(p4[:, 0],
                                                                   p4[:, 1],
                                                                   p4[:, 2],
                                                                   p4[:, 3])
        fast_pt = _fast_pt(p4)
        fast_eta = _fast_eta(p4)
        fast_phi = _fast_phi(p4)
        fast_mass = _fast_mass(p4)
    elif 'pt' in argkeys and 'eta' in argkeys and 'phi' in argkeys and 'mass' in argkeys:
        print("\n\n---- About to TLorentz")
        p4 = uproot_methods.TLorentzVectorArray.from_ptetaphim(items['pt'],
                                                               items['eta'],
                                                               items['phi'],
                                                               items['mass'])
        print("made it past TLorents")
        fast_pt = items['pt']
        fast_eta = items['eta']
        fast_phi = items['phi']
        fast_mass = items['mass']
        del items['pt']
        del items['eta']
        del items['phi']
        del items['mass']
    elif 'pt' in argkeys and 'eta' in argkeys and 'phi' in argkeys and 'energy' in argkeys:
        p4 = uproot_methods.TLorentzVectorArray.from_ptetaphi(items['pt'],
                                                              items['eta'],
                                                              items['phi'],
                                                              items['energy'])
        fast_pt = items['pt']
        fast_eta = items['eta']
        fast_phi = items['phi']
        fast_mass = _fast_mass(p4)
        del items['pt']
        del items['eta']
        del items['phi']
        del items['energy']
    elif 'px' in argkeys and 'py' in argkeys and 'pz' in argkeys and 'mass' in argkeys:
        p4 = uproot_methods.TLorentzVectorArray.from_xyzm(items['px'],
                                                          items['py'],
                                                          items['pz'],
                                                          items['mass'])
        fast_pt = _fast_pt(p4)
        fast_eta = _fast_eta(p4)
        fast_phi = _fast_phi(p4)
        fast_mass = items['mass']
        del items['px']
        del items['py']
        del items['pz']
        del items['mass']
    elif 'pt' in argkeys and 'phi' in argkeys and 'pz' in argkeys and 'energy' in argkeys:
        p4 = uproot_methods.TLorentzVectorArray.from_cylindrical(items['pt'],
                                                                 items['phi'],
                                                                 items['pz'],
                                                                 items[
                                                                     'energy'])
        fast_pt = items['pt']
        fast_eta = _fast_eta(p4)
        fast_phi = items['phi']
        fast_mass = _fast_mass(p4)
        del items['pt']
        del items['phi']
        del items['pz']
        del items['energy']
    elif 'px' in argkeys and 'py' in argkeys and 'pz' in argkeys and 'energy' in argkeys:
        p4 = uproot_methods.TLorentzVectorArray.from_cartesian(items['px'],
                                                               items['py'],
                                                               items['pz'],
                                                               items['energy'])
        fast_pt = _fast_pt(p4)
        fast_eta = _fast_eta(p4)
        fast_phi = _fast_phi(p4)
        fast_mass = _fast_mass(p4)
        del items['px']
        del items['py']
        del items['pz']
        del items['energy']
    elif 'p' in argkeys and 'theta' in argkeys and 'phi' in argkeys and 'energy' in argkeys:
        p4 = uproot_methods.TLorentzVectorArray.from_spherical(items['p'],
                                                               items['theta'],
                                                               items['phi'],
                                                               items['energy'])
        fast_pt = _fast_pt(p4)
        fast_eta = _fast_eta(p4)
        fast_phi = items['phi']
        fast_mass = _fast_mass(p4)
        del items['p']
        del items['theta']
        del items['phi']
        del items['energy']
    elif 'p3' in argkeys and 'energy' in argkeys:
        p4 = uproot_methods.TLorentzVectorArray.from_p3(items['p3'],
                                                        items['energy'])
        fast_pt = _fast_pt(p4)
        fast_eta = _fast_eta(p4)
        fast_phi = _fast_phi(p4)
        fast_mass = _fast_mass(p4)
        del items['p3']
        del items['energy']
    else:
        print("Not balid ")
        raise Exception(
            'No valid definition of four-momentum found to build JaggedCandidateArray')

    items['p4'] = p4
    items['__fast_pt'] = fast_pt
    items['__fast_eta'] = fast_eta
    items['__fast_phi'] = fast_phi
    items['__fast_mass'] = fast_mass
    return awkward.Table(items)
    # return cls.fromoffsets(offsets, awkward.Table(items))

spark = SparkSession.builder \
    .master("local") \
    .appName("spark_reader") \
    .config("spark.jars.packages",
      "org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.0") \
    .getOrCreate()


df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers","localhost:9092") \
    .option("subscribe", "serviceX") \
    .option("startingOffsets", "earliest").load()

def from_arrow(buf):
    reader = pa.ipc.open_stream(buf)
    batches = [b for b in reader]
    arrays = batches[0].to_pydict()
    offsets = awkward.JaggedArray.counts2offsets(awkward.JaggedArray.fromiter(arrays['nElectron']))
    physics_objects = {}

    physics_objects["Electron"] = \
        candidatesfromoffsets(awkward.JaggedArray.fromiter(arrays['nElectron']),
                                                      pt=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_pt"]).content,
                                                      eta=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_eta"]).content,
                                                      phi=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_phi"]).content,
                                                      mass=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_mass"]).content,
                                                      cutBased=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_cutBased"]).content,
                                                      pdgId=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_pdgId"]).content,
                                                      pfRelIso03_all=awkward.JaggedArray.fromiter(arrays[
                                                          "Electron_pfRelIso03_all"]).content)

    # try:
    #     physics_objects["Electron"] = \
    #         JaggedCandidateArray.candidatesfromcounts(awkward.JaggedArray.fromiter(arrays['nElectron']),
    #                                                   pt=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_pt"]).content,
    #                                                   eta=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_eta"]).content,
    #                                                   phi=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_phi"]).content,
    #                                                   mass=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_mass"]).content,
    #                                                   cutBased=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_cutBased"]).content,
    #                                                   pdgId=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_pdgId"]).content,
    #                                                   pfRelIso03_all=awkward.JaggedArray.fromiter(arrays[
    #                                                       "Electron_pfRelIso03_all"]).content)
    # except Exception as execpt:
    #     print("----!!!!--->",execpt)

    # electrons = physics_objects["Electron"]
    # print("---->",electrons[(electrons.pt > 20)])

    return physics_objects

spark.udf.register("from_arrow", from_arrow)

x = df.selectExpr("CAST(key AS STRING)", "from_arrow(value)")

query = x \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()

# .config("spark.jars.packages",
#         "org.diana-hep:spark-root_2.11:0.1.15, org.apache.spark:spark-streaming-kafka-0-8:2.4.1") \
