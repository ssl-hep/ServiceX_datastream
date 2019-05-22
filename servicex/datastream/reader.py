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
from fnal_column_analysis_tools.analysis_objects import JaggedCandidateArray
from kafka import KafkaConsumer
import pyarrow as pa
import awkward.arrow

consumer = KafkaConsumer("serviceX", auto_offset_reset='earliest',
                         bootstrap_servers=['localhost:9092'],
                         api_version=(0, 10), consumer_timeout_ms=1000)

for msg in consumer:
    buf = msg.value
    reader = pa.ipc.open_stream(buf)
    batches = [b for b in reader]
    arrays = awkward.fromarrow(batches[0])
    print(arrays)

    print(arrays["cutBased"])

    physics_objects = {}
    physics_objects["Electron"] = \
        JaggedCandidateArray.candidatesfromcounts(awkward.JaggedArray.fromiter(arrays['nElectron']),
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

    electrons = physics_objects["Electron"]
    print("---->",electrons[(electrons.pt > 20)])
