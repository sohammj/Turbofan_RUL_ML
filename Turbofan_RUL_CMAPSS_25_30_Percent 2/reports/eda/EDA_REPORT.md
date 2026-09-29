# Exploratory data analysis

Run `python run_eda.py` from the project directory to reproduce the tables and figures in `reports/eda/`.

The tables report per-subset engine lifetimes and training-sensor variation. The lifetime figure shows that engine histories have unequal lengths. The FD001 example plots show that sensor values vary by engine and cycle; they are illustrations, not proof that one sensor alone predicts failure.

The data are simulated run-to-failure histories. Training rows contain complete trajectories; test histories stop earlier. All model comparisons must split by engine and avoid using future cycles as input.

```text
dataset_id split  rows  engines  cycle_min  cycle_median  cycle_mean  cycle_max
     FD001 train 20631      100        128         199.0  206.310000        362
     FD001  test 13096      100         31         133.5  130.960000        303
     FD002 train 53759      260        128         199.0  206.765385        378
     FD002  test 33991      259         21         132.0  131.239382        367
     FD003 train 24720      100        145         220.5  247.200000        525
     FD003  test 16596      100         38         148.0  165.960000        475
     FD004 train 61249      249        128         234.0  245.979920        543
     FD004  test 41214      248         19         153.5  166.185484        486
```
