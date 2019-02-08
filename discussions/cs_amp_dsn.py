
import bag
from bag.data import load_sim_results
from scripts_char.mos_query import get_db
import pprint
import matplotlib.pyplot as plt


def generate(prj, temp_lib, impl_lib, cell_name, sch_params):

    print("Generating schematic ...")
    dsn = prj.create_design_module(temp_lib, cell_name)
    dsn.design(**sch_params)
    dsn.implement_design(impl_lib, top_cell_name=cell_name)


def simulate(prj, temp_lib, impl_lib, tb_name, cell_name, sim_params, show_plot=True):

    # generate tb schematic
    print("Generating testbench ...")
    dsn = prj.create_design_module(temp_lib, tb_name)
    dsn.design(impl_lib=impl_lib, cell_name=cell_name)
    dsn.implement_design(impl_lib, top_cell_name=tb_name)

    # configure tb
    tb = prj.configure_testbench(tb_lib=impl_lib, tb_cell=tb_name)
    tb.set_parameter('supply', sim_params[0])
    tb.set_parameter('in_bias', sim_params[1])
    tb.set_parameter('nf', sim_params[2])
    tb.update_testbench()

    # rum simulation
    tb.run_simulation()
    print(tb.save_dir)
    results = load_sim_results(tb.save_dir)

    out_dc = results['out_dc']
    freq = results['freq']
    out_ac_amp = results['out_ac_amp']
    out_ac_phase = results['out_ac_phase']

    if show_plot:
        print(f"Output dc is {out_dc}")
        plt.figure()
        plt.subplot(2, 1, 1)
        plt.semilogx(freq, out_ac_amp)
        plt.subplot(2, 1, 2)
        plt.semilogx(freq, out_ac_phase)
        plt.show(block=False)

    return out_dc, out_ac_amp, out_ac_phase


def design1(prj, temp_lib, impl_lib, tb_name, cell_name, sch_params):

    print("Calculate transistor number of fingers ...")

    # read database
    interp_method = 'spline'
    sim_env = 'tt'
    nmos_spec = 'specs_mos_char/nch_w0d4_45n.yaml'
    intent='lvt'
    db = get_db(nmos_spec, intent, interp_method=interp_method, sim_env=sim_env)

    # get mos bias information
    mos_info = db.query(vbs=0, vds=0.7, vgs=0.7)
    # print mos bias information
    pprint.pprint(mos_info)
    print("\n")

    # calculate
    head_room = 0.5
    res = 1e3
    nf = round(head_room / res / mos_info['ibias'])
    sch_params['nf'] = nf
    print(f"MOS finger number is {nf}")

    generate(prj, temp_lib, impl_lib, cell_name, sch_params)
    simulate(prj, temp_lib, impl_lib, tb_name, cell_name, sim_params=[1.2, 0.7, nf])


def design2(prj, temp_lib, impl_lib, tb_name, cell_name, sch_params):

    print("Calculate transistor number of fingers ...")

    generate(prj, temp_lib, impl_lib, cell_name, sch_params)

    out_dc = 1.2
    nf = 1
    nf_list = []
    out_dc_list = []
    while out_dc > 0.7:
        out_dc, out_ac_amp, out_ac_phase = \
            simulate(prj, temp_lib, impl_lib, tb_name, cell_name, sim_params=[1.2, 0.7, nf], show_plot=False)

        # add to lists
        nf_list.append(nf)
        out_dc_list.append(out_dc)
        print(f"Output dc is {out_dc} @ nf is {nf}")

        # change nf
        nf = nf+1

    # plot output dc
    plt.figure()
    plt.plot(nf_list, out_dc_list)
    plt.show(block=False)

    simulate(prj, temp_lib, impl_lib, tb_name, cell_name, sim_params=[1.2, 0.7, nf-1])


if __name__ is '__main__':

    if 'bprj' not in locals():
        bprj = bag.BagProject()

    impl_lib = 'AAAFOO_CS_AMP'
    temp_lib = 'bag_tutorial'
    cell_name = 'cs_amp'
    tb_name = 'cs_amp_tb'

    sch_params = dict(
        mos_l=45e-9,
        mos_w=400e-9,
        mos_nf='nf',
        mos_intent='lvt',
    )

    # generate(bprj, temp_lib, impl_lib, cell_name, sch_params)
    # simulate(bprj, temp_lib, impl_lib, tb_name, cell_name, sim_params=[1.2, 0.7, 4])

    # design1(bprj, temp_lib, impl_lib, tb_name, cell_name, sch_params)

    design2(bprj, temp_lib, impl_lib, tb_name, cell_name, sch_params)

