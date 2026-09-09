# WITHDRAWN — near-field entrainment for a horizontal jet

> **Withdrawn before it was run.** The observation it rests on was an
> arithmetic error: the Ricou-Spalding comparison used a mass-weighted source
> density of 40.2 kg/m3 where the model uses 2.686. Corrected, the model
> entrains **1.17 to 1.48 times** a free jet, not 4.4 to 5.4, which is inside
> the scatter of the coefficient.
>
> The temperature evidence was also invalid -- it compared a bulk model
> temperature against a peak-sensor measurement.
>
> **Nothing was implemented.** See `docs/retired/RETRACTED_46...` for the
> retraction and `docs/47` for what the evidence actually supports.

---


**Registered 2026-08-24, before any change to the entrainment closure.**
Nothing above the `RESULTS` line is to be edited afterwards.

## The observation

`docs/46` establishes, from two independent measurements, that the model
entrains **4.4 to 5.4 times** a free jet in the near field of a horizontal
release:

| method | ratio |
|---|---|
| air-to-hydrogen mass ratio implied by the measured 30 m temperature | 4.4 |
| Ricou-Spalding entrainment law, 2 to 31 m | 4.4 to 5.4 |

It is confined: the two horizontal trials (FFI 4 and 6) are 20 K too warm at
30 m, the four downward trials are within 4 K, and every trial is within 2 K
at 50 and 100 m.

## The mechanism, as far as it is understood

`slabx.submodels.entrainment.friction`, EQ 35c-35e:

    delta_u = (u_bar_ambient - cl.u) * rho_ratio
    u_mh_sq = c.c_drag_top * (delta_u**2 + v_rho**2)

The top-of-cloud drag goes as the square of the velocity difference. SLAB
derives this for a dense cloud moving at a speed comparable to the wind. Here
the exit velocity is 612 m/s against a 2.7 m/s wind, and the model decays the
jet from 612 to 21 m/s within 1.9 m where a free jet would reach about 50.

**This is a hypothesis about the cause, not an established fact.** The
predictions below are stated so that it can be wrong.

## What will be changed

A jet-phase entrainment closure, active only while the release is
momentum-dominated, replacing the dense-cloud top-drag term with a
free-jet law. The switch and the law will be fixed **before** any result is
looked at, and neither will be adjusted afterwards.

**The switch must not introduce a fitted parameter.** If a threshold is
needed it must be a ratio that is already defined in the model or in the
literature, not a number chosen to make the FFI trials work.

## Negative controls -- any one of these fails and the change is rejected

**NC1.** The ten LNG pool trials move by **less than 1 %** in LFL distance.
The published dense-gas validation rests on this closure and must not move.

**NC2.** Prairie Grass passive dispersion is **bit-identical**.

**NC3.** The four downward FFI trials (1, 3, 5, 7) change by **less than 3 K**
in 30 m temperature. **They are already right and must stay right.** This is
the control most likely to fail, because a jet closure that fires on a
downward release would break what currently works.

**NC4.** No trial that is currently inside the bent-over premise moves
outside it, and none currently outside moves inside.

## Predictions -- discriminating, stated before running

**P-J1.** The two horizontal trials reach **-20 C or colder** at 30 m
(measured -26.8 and -25.7; currently -5.3 and -5.2).

**P-J2.** The two horizontal trials reach a 30 m concentration ratio of
**0.5 or better** against measurement (currently 0.37 and 0.39).

**P-J3.** The LFL bracket result stays at **five of six**, and the required
factor stays **below 1.25**.

**P-J4.** The entrainment ratio against Ricou-Spalding falls to **between 0.5
and 2.0** over 2 to 30 m (currently 4.4 to 5.4). Below 0.5 would mean the
change has overshot into too little entrainment, which is as wrong as too
much and would also be a rejection.

## What would falsify the hypothesis

If P-J1 and P-J2 fail while NC1 to NC4 pass, the near-field temperature and
concentration are not controlled by this term and the hypothesis is wrong.
Record it and stop; do not tune the closure until the predictions pass.

## Known confounder, recorded now

**The two measurements disagree about how much air is entrained.** The 30 m
temperature implies 125 kg air per kg hydrogen; the 21 vol% concentration
implies 54. The maximum concentration and the minimum temperature are read at
different sensors and different times, so they cannot be combined, and
**neither is a target the model must hit exactly**. P-J1 and P-J2 are stated
as separate one-sided bounds for that reason.

## RESULTS

*(not yet run)*
