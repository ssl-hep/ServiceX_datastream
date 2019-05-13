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
import os

import awkward
import pyarrow as pa
import uproot

file = uproot.open(os.path.join("/Users","bengal1","dev","IRIS-HEP","data",
                                "DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root"))
events = file["Events"]
arrays = events.arrays(["nElectron",
                   "Electron_pt",
                   "Electron_eta",
                   "Electron_phi",
                   "Electron_mass",
                   "Electron_cutBased",
                   "Electron_pdgId",
                   "Electron_pfRelIso03_all"], entrystop=1000)

physics_objects = {}
print(arrays[b'Electron_pt'].__class__.__name__)
offsets = awkward.JaggedArray.counts2offsets(arrays[b'nElectron'])

physics_objects["Electron"] = {
    "pt": awkward.JaggedArray.fromoffsets(offsets, arrays[b"Electron_pt"].content),
    "eta":awkward.JaggedArray.fromoffsets(offsets, arrays[b"Electron_eta"].content),
    "phi": awkward.JaggedArray.fromoffsets(offsets, arrays[b"Electron_phi"].content),
    "mass": awkward.JaggedArray.fromoffsets(offsets, arrays[b"Electron_mass"].content),
    "cutBased": awkward.JaggedArray.fromoffsets(offsets, arrays[
        b"Electron_cutBased"].content),
    "pdgId": awkward.JaggedArray.fromoffsets(offsets, arrays[b"Electron_pdgId"].content),
    "pfRelIso03_all": awkward.JaggedArray.fromoffsets(offsets, arrays[
        b"Electron_pfRelIso03_all"].content)
}

electrons = physics_objects["Electron"]
t = awkward.Table(electrons)
pa_table = awkward.toarrow(t)

batches = pa_table.to_batches()
for batch in batches:
    sink = pa.BufferOutputStream()
    writer = pa.RecordBatchStreamWriter(sink, batch.schema)
    writer.write_batch(batch)

    writer.close()
    buf = sink.getvalue()

    reader = pa.ipc.open_stream(buf)
    batches = [b for b in reader]
    arrays = awkward.fromarrow(batches[0])
    print(arrays)
