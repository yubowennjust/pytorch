# Copyright (c) 2016-present, Facebook, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from caffe2.python import core, workspace, test_util

from caffe2.python.transformations import addNNPACK, fuseNNPACKConvRelu

def str_compare(a, b, encoding="utf8"):
    if isinstance(a, bytes):
        a = a.decode(encoding)
    if isinstance(b, bytes):
        b = b.decode(encoding)
    return a == b

class TestTransformations(test_util.TestCase):
    def test_addNNPACK(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y2"])
        addNNPACK(net)
        assert str_compare(net.Proto().op[0].engine, "NNPACK")


    def test_fuseNNPACKConvRelu(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y2"])
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 1)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation"):
                assert str_compare(arg.s, "Relu")
                has_activation_arg = True
        assert has_activation_arg

    def test_noFuseNNPACKConvRelu(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y2"])
        net.Relu(["Y"], ["Y3"])
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 3)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation") and str_compare(arg.s, "Relu"):
                has_activation_arg = True
        assert not has_activation_arg

    def test_fuseNNPACKConvReluNoInplace(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["X"])
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 1)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation"):
                assert str_compare(arg.s, "Relu")
                has_activation_arg = True
        assert has_activation_arg
        assert net.Proto().op[0].output[0] != net.Proto().op[0].input[0]

    def test_fuseNNPACKConvReluInplaceRelu(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y"])
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 1)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation"):
                assert str_compare(arg.s, "Relu")
                has_activation_arg = True
        assert has_activation_arg
        assert net.Proto().op[0].output[0] != net.Proto().op[0].input[0]

    def test_fuseNNPACKConvReluPingPongNaming(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["X"])
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 2)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation"):
                assert str_compare(arg.s, "Relu")
                has_activation_arg = True
        assert has_activation_arg
        assert net.Proto().op[0].output[0] != net.Proto().op[0].input[0]
        assert net.Proto().op[1].output[0] != net.Proto().op[1].input[0]

    def test_fuseNNPACKConvReluFollowedByMultipleInputOp(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y2"])
        net.Conv(
            ["Y2", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y2"])
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 2)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation"):
                assert str_compare(arg.s, "Relu")
                has_activation_arg = True
        assert has_activation_arg
        assert net.Proto().op[0].output[0] != net.Proto().op[0].input[0]
        assert net.Proto().op[1].output[0] != net.Proto().op[1].input[0]

    def test_fuseNNPACKConvReluInplaceFollowedByMultipleInputOp(self):
        net = core.Net("net")
        net.Conv(
            ["X", "w", "b"], ["Y"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y"], ["Y"])
        net.Conv(
            ["Y", "w", "b"], ["Y2"], stride=1, pad=0, kernel=3, order="NCHW"
        )
        net.Relu(["Y2"], ["Y2"])
        addNNPACK(net) # get the NNPACK engine
        assert str_compare(net.Proto().op[0].engine, "NNPACK")
        fuseNNPACKConvRelu(net)
        assert (len(net.Proto().op) == 2)
        has_activation_arg = False
        for arg in net.Proto().op[0].arg:
            if str_compare(arg.name, "activation"):
                assert str_compare(arg.s, "Relu")
                has_activation_arg = True
        assert has_activation_arg
        assert net.Proto().op[0].output[0] != net.Proto().op[0].input[0]
        assert net.Proto().op[1].output[0] != net.Proto().op[1].input[0]
