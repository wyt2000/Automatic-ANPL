class CONFIG:

    # Agent
    gen_pretest             = {
        'temperature'       : 0.6,
    }
    gen_solution            = {
        'temperature'       : 0.6,
        'logit_bias'        : {755:-100},
    }
    gen_anpl                = {
        'temperature'       : 0.2,
        'presence_penalty'  : 0.1,
    }
    gen_anpl_with_asserts   = {
        'temperature'       : 0.6,
    }
    gen_function            = {
        'temperature'       : 0.6,
    }
    gen_counterexample      = {
        'temperature'       : 0.6,
    }
    debug_function          = {
        'temperature'       : 0.6, 
    } 
    debug_solution          = {
        'temperature'       : 0.6,
        'logit_bias'        : {755:-100}
    } 

    # Strategy
    max_restart_times: int          = 3
    max_solution_debug_times: int   = 0
    max_program_debug_times: int    = 2
    num_generated_funcs: int        = 16
    num_debugged_funcs: int         = 8
    num_pretests: int               = 100
    eval_max_attempts: int          = 100000
    eval_max_time: float            = 240
    use_pretests_debug: bool        = True

    # Misc    
    seed = 42

