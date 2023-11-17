class Config:
    gen_pretest  = {
        'temperature'       : 0.6,
    }
    gen_solution = {
        'temperature'       : 0.6,
        'logit_bias'        : {755:-100},
    }
    gen_anpl     = {
        'temperature'       : 0.2,
        'presence_penalty'  : 0.1,
    }
    gen_function = {
        'temperature'       : 0.6,
    }
    gen_counterexample = {
        'temperature'       : 0.6,
    }
    debug_function = {
        'temperature'       : 0.6, 
    } 
    debug_solution = {
        'temperature'   : 0.6,
        'logit_bias'    : {755:-100}
    } 
