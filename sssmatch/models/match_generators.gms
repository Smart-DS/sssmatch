*-------------------------------------------------------------------------------
* [LICENSE]
* Copyright (c) 2017 Alliance for Sustainable Energy, LLC. All rights reserved.
* 
* NOTICE: This software was developed at least in part by Alliance for Sustainable Energy, LLC (“Alliance”) under Contract No. DE-AC36-08GO28308 with the U.S. Department of Energy and the U.S. Government retains for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in the software to reproduce, prepare derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
* 
* Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
* 
* 1. Redistributions of source code must retain the above copyright notice, the above government rights notice, this list of conditions and the following disclaimer.
* 
* 2. Redistributions in binary form must reproduce the above copyright notice, the above government rights notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
* 
* 3.  Redistribution of this software, without modification, must refer to the software by the same designation. Redistribution of a modified version of this software (i) may not refer to the modified version by the same designation, or by any confusingly similar designation, and (ii) must refer to the underlying software originally provided by Alliance as “sssmatch”. Except to comply with the foregoing, the term “sssmatch”, or any confusingly similar designation may not be used to refer to any modified version of this software or any modified version of the underlying software originally provided by Alliance without the prior written consent of Alliance.
* 
* 4.  The name of the copyright holder, contributors, the United States Government, the United States Department of Energy, or any of their employees may not be used to endorse or promote products derived from this software without specific prior written permission.
* 
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER, CONTRIBUTORS, UNITED STATES GOVERNMENT OR UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
* [/LICENSE]
*-------------------------------------------------------------------------------

Set
    n nodes
    g generator types

    g_indep(g) generator types that can be placed independent of renewable resource locations
    g_dep(g) generator types that must be co-located with renewable resources

    allowed(n,g)
;

$gdxin 'in.gdx'
$loaddc n
$loaddc g
$loaddc g_indep
$loaddc g_dep
$gdxin

alias(g,gg) ;

Parameter
    desired_capacity(g) --MW-- desired capacity by type g
    current_capacity(n,g) --MW-- current capacity by node n and type g

    g_dist(g,gg) --unitless-- weight to count a swap from type g to type gg

    current_indep_capacity(n) --MW-- current amount of g_indep capacity
    maximum_capacity(n,g_dep) --MW-- maximum amount of g_dep capacity that may be placed at n
;

$gdxin 'in.gdx'
$loaddc desired_capacity
$loaddc current_capacity
$loaddc g_dist
$loaddc current_indep_capacity
$loaddc maximum_capacity
$gdxin

current_indep_capacity(n) = sum(g_indep,current_capacity(n,g_indep)) ;
maximum_capacity(n,g_dep) = max(maximum_capacity(n,g_dep),current_capacity(n,g_dep)) ;

allowed(n,g) = NO ;
allowed(n,g_indep)$current_indep_capacity(n) = YES ;
allowed(n,g_dep)$maximum_capacity(n,g_dep) = YES ;

execute_unload 'preproc.gdx', current_indep_capacity, maximum_capacity, allowed ;

Variable
    Distance
;

Positive variable
    Capacity(n,g) --MW-- capacity of type g at node n in the final mix

    CapacityKept(n,g) --MW-- capacity of type g at node n in original system that is kept
    CapacitySwapped(n,g,gg) --MW-- capacity that started as type g swapped for type gg at node n
    CapacityRemoved(n,g) --MW-- capacity of type g at node n that is removed for the final mix
    CapacityAdded(n,gg) --MW-- capacity of type gg that is added to node n to make the final mix
;

CapacitySwapped.fx(n,g,g)$current_capacity(n,g) = 0 ;

Equation
    match_desired_capacity(g)
    calculate_final_capacity(n,g)

    disposition_of_current_capacity(n,g)

    limit_indep_capacity(n)
    limit_dep_capacity(n,g_dep)

    capacity_distance
;

match_desired_capacity(g)..
    sum(n$allowed(n,g),Capacity(n,g)) =e= desired_capacity(g) ;

calculate_final_capacity(n,g)$allowed(n,g)..
    Capacity(n,g) 
  =e= 
    CapacityKept(n,g) + 
    sum(gg$current_capacity(n,gg),CapacitySwapped(n,gg,g)) + 
    CapacityAdded(n,g) ;

disposition_of_current_capacity(n,g)$allowed(n,g)..
    CapacityKept(n,g) + sum(gg$allowed(n,gg),CapacitySwapped(n,g,gg)) + CapacityRemoved(n,g) 
  =e= 
    current_capacity(n,g) ;

limit_indep_capacity(n)..
    sum(g_indep$allowed(n,g_indep),Capacity(n,g_indep)) 
  =l= 
    current_indep_capacity(n) ;

limit_dep_capacity(n,g_dep)$allowed(n,g_dep)..
    Capacity(n,g_dep) =l= maximum_capacity(n,g_dep) ;

capacity_distance..
    Distance 
  =e= 
    sum((n,g)$allowed(n,g),CapacityAdded(n,g) + CapacityRemoved(n,g)) + 
    sum((n,g,gg)$(current_capacity(n,g) and allowed(n,gg)),CapacitySwapped(n,g,gg)*g_dist(g,gg)) ;

Model MatchGenerationMix /
    match_desired_capacity
    calculate_final_capacity

    disposition_of_current_capacity

    limit_indep_capacity
    limit_dep_capacity

    capacity_distance
/ ;

option savepoint=1 ;
option solprint=off ;
Solve MatchGenerationMix using lp minimizing Distance ;

