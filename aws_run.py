import asdf

from weldx.constants import WELDX_QUANTITY as _Q

from weldx.asdf.extension import WeldxExtension
from weldx.asdf.tags.weldx.aws.process.gas_component import GasComponent
from weldx.asdf.tags.weldx.aws.process.shielding_gas_type import ShieldingGasType
from weldx.asdf.tags.weldx.aws.process.shielding_gas_for_procedure import (
    ShieldingGasForProcedure,
)

gas_comp = [GasComponent("Argon", 82.0), GasComponent("Carbon Dioxide", 18.0)]
gas_type = ShieldingGasType(gas_component=gas_comp, common_name="SG")

"""
gas_for_procedure = ShieldingGasForProcedure(
    use_torch_shielding_gas=True,
    torch_shielding_gas=gas_type,
    torch_shielding_gas_flowrate=_Q(20, "l/min"),
)
"""

filename = "aws_demo.asdf"
tree = dict(entry=gas_type)

# Write the data to a new file
with asdf.AsdfFile(
    tree, extensions=[WeldxExtension()], ignore_version_mismatch=False
) as ff:
    ff.write_to(filename, all_array_storage="inline")

# read back data from ASDF file
with asdf.open(filename, copy_arrays=True, extensions=[WeldxExtension()]) as af:
    data = af.tree
    print(data["entry"])
