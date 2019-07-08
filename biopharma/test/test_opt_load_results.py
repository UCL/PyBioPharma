
# from conftest import *


def test_run_opt_load_results(default_model):
    """
    This test checks that we can serialise optimiser results to YAML and reload,
    getting the same information after loading.

    It also checks that resetting the seed and re-running gives the same results.
    """
    facility, product, steps = default_model

    # Set up the optimiser
    from biopharma import optimisation as opt

    optimiser = opt.Optimiser(facility)

    # Specify the variables to optimise.
    optimiser.add_variable(
        gen=opt.gen.Binary(), component=opt.sel.step('test_step'), item='bool_param')
    optimiser.add_variable(gen=opt.gen.RangeGenerator(0, 10),
                           component=opt.sel.step('test_step'), item='int_param')

    # Specify the objective(s)
    optimiser.add_objective(component=opt.sel.product(0), item='cogs', minimise=True)

    # Run optimisation
    optimiser.parameters['populationSize'] = 2
    optimiser.parameters['maxGenerations'] = 1
    optimiser.run()

    original_pop = optimiser.outputs['finalPopulation']
    original_best_fitness = optimiser.outputs['bestObjectiveValues']

    # Save results and re-load
    results = optimiser.save_results()
    optimiser.load_results(results)

    # Check loaded individuals are distinct but equivalent
    for orig, loaded in zip(original_pop, optimiser.outputs['finalPopulation']):
        assert orig is not loaded
        assert orig == loaded
    assert original_best_fitness == optimiser.outputs['bestObjectiveValues']

    # Reset the seed and re-run
    optimiser.set_seed(optimiser.outputs['seed'])
    optimiser.run()

    # Check for equivalent individuals again
    for orig, rerun in zip(original_pop, optimiser.outputs['finalPopulation']):
        assert orig is not rerun
        assert orig == rerun
    # And as an extra sanity check, verify we get the same fitness for the best solution
    assert original_best_fitness == optimiser.outputs['bestObjectiveValues']
