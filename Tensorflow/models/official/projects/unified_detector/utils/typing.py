# Copyright 2022 The TensorFlow Authors. All Rights Reserved.
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

"""Typing extension."""

from typing import Dict, Union

import numpy as np
import tensorflow as tf

NpDict = Dict[str, np.ndarray]
FeaturesAndLabelsType = Dict[str, Dict[str, tf.Tensor]]
TensorDict = Dict[Union[str, int], tf.Tensor]
NestedTensorDict = Dict[
    Union[str, int],
    Union[tf.Tensor,
          TensorDict]]
