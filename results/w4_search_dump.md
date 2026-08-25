# Week 4 search-only dump: 30 questions, both modes

Depth 10 searched, hit-rate graded at 3. `ANSWER` marks the chunk that satisfies the hit rule.

---

## W1 - `MIG-100`

**Question:** An account shows the MIG-100 badge. What does it mean and what should the agent do?

**Known-correct location:** `HC-4001` -> Migration status codes -> MIG-100

**Hit requires:** `MIG-100`, `Treat the account as normal`

### dense -> HIT at rank 1

- 1. score 0.8263  `HC-4001-structured-005`  HC-4001  [ANSWER]
- 2. score 0.6616  `HC-4001-structured-004`  HC-4001
- 3. score 0.6290  `HC-4004-structured-005`  HC-4004
- 4. score 0.6176  `HC-4005-structured-003`  HC-4005
- 5. score 0.6041  `HC-4001-structured-002`  HC-4001
- 6. score 0.5951  `HC-4003-structured-004`  HC-4003
- 7. score 0.5943  `HC-4003-structured-005`  HC-4003
- 8. score 0.5907  `HC-4002-structured-005`  HC-4002
- 9. score 0.5870  `HC-4005-structured-005`  HC-4005
- 10. score 0.5847  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4001-structured-005`  HC-4001  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8263 kw=19.4522
- 2. score 0.0311  `HC-4001-structured-004`  HC-4001  [both]  dense_rank=2 kw_rank=7 dense=0.6616 kw=7.08
- 3. score 0.0304  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=10 kw_rank=2 dense=0.5847 kw=11.9125
- 4. score 0.0301  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=5 kw_rank=8 dense=0.6041 kw=6.7633
- 5. score 0.0299  `HC-4005-structured-005`  HC-4005  [both]  dense_rank=9 kw_rank=5 dense=0.587 kw=7.9425
- 6. score 0.0297  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=11 kw_rank=4 dense=0.5787 kw=8.4162
- 7. score 0.0290  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=3 kw_rank=16 dense=0.629 kw=3.7419
- 8. score 0.0284  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=8 kw_rank=13 dense=0.5907 kw=4.6132
- 9. score 0.0283  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=7 kw_rank=15 dense=0.5943 kw=3.862
- 10. score 0.0258  `HC-4004-structured-003`  HC-4004  [both]  dense_rank=16 kw_rank=19 dense=0.5607 kw=3.3226

---

## W2 - `MIG-140`

**Question:** What does the MIG-140 badge mean, and do we need to do anything about it?

**Known-correct location:** `HC-4001` -> Migration status codes -> MIG-140

**Hit requires:** `MIG-140`, `Explain the write-off`

### dense -> HIT at rank 1

- 1. score 0.7493  `HC-4001-structured-005`  HC-4001  [ANSWER]
- 2. score 0.6072  `HC-4001-structured-004`  HC-4001
- 3. score 0.5828  `HC-4004-structured-005`  HC-4004
- 4. score 0.5816  `HC-4003-structured-004`  HC-4003
- 5. score 0.5770  `HC-4005-structured-003`  HC-4005
- 6. score 0.5609  `HC-4002-structured-004`  HC-4002
- 7. score 0.5567  `HC-4001-structured-002`  HC-4001
- 8. score 0.5517  `HC-4003-structured-005`  HC-4003
- 9. score 0.5483  `HC-4002-structured-005`  HC-4002
- 10. score 0.5396  `HC-4005-structured-005`  HC-4005

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4001-structured-005`  HC-4001  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7493 kw=17.607
- 2. score 0.0311  `HC-4001-structured-004`  HC-4001  [both]  dense_rank=2 kw_rank=7 dense=0.6072 kw=5.6442
- 3. score 0.0295  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=12 kw_rank=4 dense=0.5349 kw=6.5005
- 4. score 0.0293  `HC-4003-structured-001`  HC-4003  [both]  dense_rank=16 kw_rank=2 dense=0.5304 kw=13.9664
- 5. score 0.0291  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=4 kw_rank=14 dense=0.5816 kw=3.5713
- 6. score 0.0290  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=7 kw_rank=11 dense=0.5567 kw=4.2695
- 7. score 0.0290  `HC-4005-structured-005`  HC-4005  [both]  dense_rank=10 kw_rank=8 dense=0.5396 kw=5.3654
- 8. score 0.0287  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=18 kw_rank=3 dense=0.5265 kw=7.9743
- 9. score 0.0286  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=8 kw_rank=12 dense=0.5517 kw=4.1589
- 10. score 0.0285  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=5 kw_rank=16 dense=0.577 kw=3.1476

---

## W3 - `MIG-220`

**Question:** An account is showing MIG-220. What went wrong and what is the agent action?

**Known-correct location:** `HC-4001` -> Migration status codes -> MIG-220

**Hit requires:** `MIG-220`, `Do not reissue invoices yourself`

### dense -> HIT at rank 1

- 1. score 0.7985  `HC-4001-structured-005`  HC-4001  [ANSWER]
- 2. score 0.7320  `HC-4004-structured-005`  HC-4004
- 3. score 0.6606  `HC-4002-structured-005`  HC-4002
- 4. score 0.6585  `HC-4005-structured-003`  HC-4005
- 5. score 0.6564  `HC-4003-structured-005`  HC-4003
- 6. score 0.6545  `HC-4001-structured-002`  HC-4001
- 7. score 0.6393  `HC-4006-structured-002`  HC-4006
- 8. score 0.6366  `HC-4003-structured-004`  HC-4003
- 9. score 0.6186  `HC-4006-structured-004`  HC-4006
- 10. score 0.6113  `HC-4002-structured-004`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4001-structured-005`  HC-4001  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7985 kw=17.6695
- 2. score 0.0302  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=2 kw_rank=11 dense=0.732 kw=2.8803
- 3. score 0.0301  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=4 kw_rank=9 dense=0.6585 kw=3.9745
- 4. score 0.0298  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=12 dense=0.6606 kw=2.8163
- 5. score 0.0298  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=12 kw_rank=3 dense=0.6061 kw=6.4842
- 6. score 0.0287  `HC-4006-structured-001`  HC-4006  [both]  dense_rank=14 kw_rank=6 dense=0.6 kw=4.6369
- 7. score 0.0285  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=6 kw_rank=15 dense=0.6545 kw=2.1566
- 8. score 0.0284  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=5 kw_rank=17 dense=0.6564 kw=1.9894
- 9. score 0.0275  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=18 kw_rank=8 dense=0.5889 kw=4.1706
- 10. score 0.0262  `HC-4003-structured-003`  HC-4003  [both]  dense_rank=13 kw_rank=20 dense=0.6002 kw=1.8115

---

## W4 - `MIG-310`

**Question:** A customer badge says MIG-310. How long should we wait before escalating?

**Known-correct location:** `HC-4001` -> Migration status codes -> MIG-310

**Hit requires:** `MIG-310`, `Wait one night`

### dense -> HIT at rank 1

- 1. score 0.8141  `HC-4001-structured-005`  HC-4001  [ANSWER]
- 2. score 0.6734  `HC-4004-structured-005`  HC-4004
- 3. score 0.6624  `HC-4001-structured-002`  HC-4001
- 4. score 0.6540  `HC-4006-structured-005`  HC-4006
- 5. score 0.6454  `HC-4003-structured-004`  HC-4003
- 6. score 0.6443  `HC-4003-structured-003`  HC-4003
- 7. score 0.6423  `HC-4005-structured-003`  HC-4005
- 8. score 0.6391  `HC-4002-structured-005`  HC-4002
- 9. score 0.6389  `HC-4003-structured-005`  HC-4003
- 10. score 0.6209  `HC-4002-structured-004`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4001-structured-005`  HC-4001  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8141 kw=17.1714
- 2. score 0.0310  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=3 kw_rank=6 dense=0.6624 kw=4.6418
- 3. score 0.0306  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=2 kw_rank=9 dense=0.6734 kw=2.7334
- 4. score 0.0300  `HC-4001-structured-004`  HC-4001  [both]  dense_rank=11 kw_rank=3 dense=0.6188 kw=5.3902
- 5. score 0.0295  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=5 kw_rank=11 dense=0.6454 kw=2.4134
- 6. score 0.0286  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=20 kw_rank=2 dense=0.5864 kw=5.669
- 7. score 0.0286  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=8 kw_rank=12 dense=0.6391 kw=2.0728
- 8. score 0.0284  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=7 kw_rank=14 dense=0.6423 kw=1.0972
- 9. score 0.0277  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=9 kw_rank=16 dense=0.6389 kw=1.078
- 10. score 0.0276  `HC-4003-structured-001`  HC-4003  [both]  dense_rank=19 kw_rank=7 dense=0.5924 kw=3.7999

---

## W5 - `MIG-450`

**Question:** What does MIG-450 mean, and can the customer still change their plan?

**Known-correct location:** `HC-4001` -> Migration status codes -> MIG-450

**Hit requires:** `MIG-450`, `Escalate to Billing Ops immediately`

### dense -> HIT at rank 1

- 1. score 0.7651  `HC-4001-structured-005`  HC-4001  [ANSWER]
- 2. score 0.7124  `HC-4004-structured-005`  HC-4004
- 3. score 0.6841  `HC-4001-structured-002`  HC-4001
- 4. score 0.6555  `HC-4002-structured-004`  HC-4002
- 5. score 0.6500  `HC-4006-structured-002`  HC-4006
- 6. score 0.6371  `HC-4001-structured-001`  HC-4001
- 7. score 0.6361  `HC-4002-structured-005`  HC-4002
- 8. score 0.6358  `HC-4005-structured-001`  HC-4005
- 9. score 0.6344  `HC-4006-structured-003`  HC-4006
- 10. score 0.6310  `HC-4003-structured-004`  HC-4003

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4001-structured-005`  HC-4001  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7651 kw=13.8071
- 2. score 0.0323  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=2 kw_rank=2 dense=0.7124 kw=8.2038
- 3. score 0.0317  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=3 kw_rank=3 dense=0.6841 kw=8.191
- 4. score 0.0308  `HC-4001-structured-001`  HC-4001  [both]  dense_rank=6 kw_rank=4 dense=0.6371 kw=5.8162
- 5. score 0.0295  `HC-4004-structured-001`  HC-4004  [both]  dense_rank=11 kw_rank=5 dense=0.6307 kw=5.5782
- 6. score 0.0286  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=10 kw_rank=10 dense=0.631 kw=4.3914
- 7. score 0.0284  `HC-4001-structured-006`  HC-4001  [both]  dense_rank=14 kw_rank=7 dense=0.6126 kw=5.0994
- 8. score 0.0284  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=7 kw_rank=14 dense=0.6361 kw=3.5652
- 9. score 0.0275  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=8 kw_rank=18 dense=0.6358 kw=3.1964
- 10. score 0.0265  `HC-4004-structured-002`  HC-4004  [both]  dense_rank=15 kw_rank=16 dense=0.6079 kw=3.4604

---

## W6 - `ERR-4010`

**Question:** An invoice is stuck on ERR-4010. What is the cause and how do we clear it?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4010

**Hit requires:** `ERR-4010`, `Customer Details`

### dense -> HIT at rank 1

- 1. score 0.7937  `HC-4002-structured-004`  HC-4002  [ANSWER]
- 2. score 0.7933  `HC-4005-structured-004`  HC-4005
- 3. score 0.7827  `HC-4002-structured-005`  HC-4002
- 4. score 0.7799  `HC-4002-structured-006`  HC-4002
- 5. score 0.7376  `HC-4002-structured-007`  HC-4002
- 6. score 0.7356  `HC-4004-structured-005`  HC-4004
- 7. score 0.7286  `HC-4005-structured-003`  HC-4005
- 8. score 0.7233  `HC-4002-structured-003`  HC-4002
- 9. score 0.7201  `HC-4003-structured-005`  HC-4003
- 10. score 0.7186  `HC-4006-structured-004`  HC-4006

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4002-structured-004`  HC-4002  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7937 kw=12.1502
- 2. score 0.0315  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=4 kw_rank=3 dense=0.7799 kw=8.8081
- 3. score 0.0313  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=5 dense=0.7827 kw=7.6586
- 4. score 0.0310  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=5 kw_rank=4 dense=0.7376 kw=8.2283
- 5. score 0.0308  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=8 dense=0.7933 kw=7.0693
- 6. score 0.0295  `HC-4005-structured-005`  HC-4005  [both]  dense_rank=15 kw_rank=2 dense=0.6568 kw=11.0368
- 7. score 0.0294  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=6 kw_rank=10 dense=0.7356 kw=6.3693
- 8. score 0.0290  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=7 kw_rank=11 dense=0.7286 kw=6.1198
- 9. score 0.0284  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=12 kw_rank=9 dense=0.6942 kw=6.6599
- 10. score 0.0282  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=9 kw_rank=13 dense=0.7201 kw=5.841

---

## W7 - `ERR-4021`

**Question:** What causes ERR-4021 on an invoice, and what is the correct fix?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4021

**Hit requires:** `ERR-4021`, `Rebuild Usage`

### dense -> MISS (answer at rank 4)

- 1. score 0.7913  `HC-4002-structured-006`  HC-4002
- 2. score 0.7891  `HC-4005-structured-004`  HC-4005
- 3. score 0.7832  `HC-4002-structured-005`  HC-4002
- 4. score 0.7819  `HC-4002-structured-004`  HC-4002  [ANSWER]
- 5. score 0.7308  `HC-4002-structured-007`  HC-4002
- 6. score 0.7234  `HC-4005-structured-003`  HC-4005
- 7. score 0.6987  `HC-4004-structured-005`  HC-4004
- 8. score 0.6953  `HC-4002-structured-003`  HC-4002
- 9. score 0.6898  `HC-4003-structured-004`  HC-4003
- 10. score 0.6884  `HC-4003-structured-005`  HC-4003

### hybrid -> HIT at rank 3

- 1. score 0.0320  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=3 dense=0.7891 kw=9.0968
- 2. score 0.0318  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=5 kw_rank=1 dense=0.7308 kw=12.4388
- 3. score 0.0318  `HC-4002-structured-004`  HC-4002  [ANSWER, both]  dense_rank=4 kw_rank=2 dense=0.7819 kw=11.319
- 4. score 0.0315  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=4 dense=0.7832 kw=8.976
- 5. score 0.0307  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=1 kw_rank=10 dense=0.7913 kw=6.1569
- 6. score 0.0303  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=6 kw_rank=6 dense=0.7234 kw=6.6452
- 7. score 0.0294  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=7 kw_rank=9 dense=0.6987 kw=6.2307
- 8. score 0.0292  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=10 kw_rank=7 dense=0.6884 kw=6.5901
- 9. score 0.0285  `HC-4005-structured-005`  HC-4005  [both]  dense_rank=16 kw_rank=5 dense=0.6398 kw=7.6127
- 10. score 0.0284  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=9 kw_rank=12 dense=0.6898 kw=5.0022

---

## W8 - `ERR-4032`

**Question:** A customer sees ERR-4032 on their invoice. What is the cause and the fix?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4032

**Hit requires:** `ERR-4032`, `reissue the invoice`

### dense -> HIT at rank 3

- 1. score 0.7837  `HC-4002-structured-005`  HC-4002
- 2. score 0.7646  `HC-4005-structured-004`  HC-4005
- 3. score 0.7620  `HC-4002-structured-004`  HC-4002  [ANSWER]
- 4. score 0.7425  `HC-4002-structured-006`  HC-4002
- 5. score 0.7216  `HC-4003-structured-005`  HC-4003
- 6. score 0.7047  `HC-4004-structured-005`  HC-4004
- 7. score 0.7000  `HC-4005-structured-003`  HC-4005
- 8. score 0.6991  `HC-4002-structured-007`  HC-4002
- 9. score 0.6763  `HC-4003-structured-004`  HC-4003
- 10. score 0.6729  `HC-4002-structured-003`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0323  `HC-4002-structured-004`  HC-4002  [ANSWER, both]  dense_rank=3 kw_rank=1 dense=0.762 kw=13.7473
- 2. score 0.0323  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=1 kw_rank=3 dense=0.7837 kw=8.7148
- 3. score 0.0318  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=4 dense=0.7646 kw=8.6757
- 4. score 0.0306  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=9 kw_rank=2 dense=0.6763 kw=8.7271
- 5. score 0.0305  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=5 kw_rank=6 dense=0.7216 kw=7.3651
- 6. score 0.0303  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=4 kw_rank=8 dense=0.7425 kw=7.1289
- 7. score 0.0303  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=7 kw_rank=5 dense=0.7 kw=8.6488
- 8. score 0.0301  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=6 kw_rank=7 dense=0.7047 kw=7.1788
- 9. score 0.0288  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=8 kw_rank=11 dense=0.6991 kw=5.0471
- 10. score 0.0278  `HC-4001-structured-006`  HC-4001  [both]  dense_rank=15 kw_rank=9 dense=0.6315 kw=6.7171

---

## W9 - `ERR-4044`

**Question:** An invoice shows ERR-4044 with a negative total. What should the agent do?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4044

**Hit requires:** `ERR-4044`, `Apply as Credit`

### dense -> HIT at rank 1

- 1. score 0.8113  `HC-4002-structured-005`  HC-4002  [ANSWER]
- 2. score 0.7648  `HC-4005-structured-004`  HC-4005
- 3. score 0.7468  `HC-4002-structured-006`  HC-4002
- 4. score 0.7412  `HC-4002-structured-004`  HC-4002
- 5. score 0.7391  `HC-4002-structured-007`  HC-4002
- 6. score 0.7205  `HC-4005-structured-003`  HC-4005
- 7. score 0.7120  `HC-4004-structured-005`  HC-4004
- 8. score 0.7014  `HC-4003-structured-005`  HC-4003
- 9. score 0.6776  `HC-4003-structured-004`  HC-4003
- 10. score 0.6752  `HC-4002-structured-001`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4002-structured-005`  HC-4002  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8113 kw=16.1128
- 2. score 0.0315  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=5 kw_rank=2 dense=0.7391 kw=10.9098
- 3. score 0.0304  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=3 kw_rank=9 dense=0.7468 kw=5.4805
- 4. score 0.0297  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=10 kw_rank=5 dense=0.6752 kw=7.3858
- 5. score 0.0296  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=14 dense=0.7648 kw=4.4584
- 6. score 0.0294  `HC-4001-structured-006`  HC-4001  [both]  dense_rank=14 kw_rank=3 dense=0.6676 kw=9.003
- 7. score 0.0292  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=6 kw_rank=11 dense=0.7205 kw=5.34
- 8. score 0.0292  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=7 kw_rank=10 dense=0.712 kw=5.4619
- 9. score 0.0286  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=17 kw_rank=4 dense=0.6575 kw=8.6555
- 10. score 0.0284  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=4 kw_rank=18 dense=0.7412 kw=3.7333

---

## W10 - `ERR-4055`

**Question:** We are seeing ERR-4055 on overlapping billing periods. Which invoice do we void?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4055

**Hit requires:** `ERR-4055`, `Void the newer invoice`

### dense -> HIT at rank 1

- 1. score 0.8143  `HC-4002-structured-005`  HC-4002  [ANSWER]
- 2. score 0.7617  `HC-4002-structured-007`  HC-4002
- 3. score 0.7492  `HC-4002-structured-004`  HC-4002
- 4. score 0.7452  `HC-4005-structured-004`  HC-4005
- 5. score 0.7445  `HC-4002-structured-006`  HC-4002
- 6. score 0.7358  `HC-4006-structured-002`  HC-4006
- 7. score 0.7199  `HC-4001-structured-002`  HC-4001
- 8. score 0.7184  `HC-4004-structured-005`  HC-4004
- 9. score 0.7176  `HC-4005-structured-003`  HC-4005
- 10. score 0.7138  `HC-4003-structured-005`  HC-4003

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4002-structured-005`  HC-4002  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8143 kw=13.4943
- 2. score 0.0320  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=3 kw_rank=2 dense=0.7492 kw=9.8113
- 3. score 0.0310  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=5 kw_rank=4 dense=0.7445 kw=7.2361
- 4. score 0.0306  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=2 kw_rank=9 dense=0.7617 kw=5.5727
- 5. score 0.0290  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=4 kw_rank=15 dense=0.7452 kw=3.6722
- 6. score 0.0288  `HC-4006-structured-004`  HC-4006  [both]  dense_rank=11 kw_rank=8 dense=0.7133 kw=5.6742
- 7. score 0.0286  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=8 kw_rank=12 dense=0.7184 kw=4.2527
- 8. score 0.0286  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=9 kw_rank=11 dense=0.7176 kw=4.3785
- 9. score 0.0286  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=10 kw_rank=10 dense=0.7138 kw=4.5595
- 10. score 0.0284  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=7 kw_rank=14 dense=0.7199 kw=3.9384

---

## W11 - `ERR-4061`

**Question:** What does ERR-4061 mean, and can an agent fix it themselves?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4061

**Hit requires:** `ERR-4061`, `cannot change invoice currency`

### dense -> HIT at rank 1

- 1. score 0.7392  `HC-4002-structured-005`  HC-4002  [ANSWER]
- 2. score 0.7327  `HC-4004-structured-005`  HC-4004
- 3. score 0.7238  `HC-4002-structured-004`  HC-4002
- 4. score 0.7179  `HC-4005-structured-004`  HC-4005
- 5. score 0.7142  `HC-4002-structured-006`  HC-4002
- 6. score 0.7041  `HC-4003-structured-004`  HC-4003
- 7. score 0.6938  `HC-4001-structured-005`  HC-4001
- 8. score 0.6905  `HC-4005-structured-003`  HC-4005
- 9. score 0.6877  `HC-4003-structured-005`  HC-4003
- 10. score 0.6872  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4002-structured-005`  HC-4002  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7392 kw=12.157
- 2. score 0.0318  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=2 kw_rank=4 dense=0.7327 kw=5.8915
- 3. score 0.0315  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=5 kw_rank=2 dense=0.7142 kw=8.6745
- 4. score 0.0310  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=6 kw_rank=3 dense=0.7041 kw=6.313
- 5. score 0.0310  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=4 kw_rank=5 dense=0.7179 kw=5.0934
- 6. score 0.0304  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=3 kw_rank=9 dense=0.7238 kw=4.4415
- 7. score 0.0294  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=10 kw_rank=6 dense=0.6872 kw=5.0104
- 8. score 0.0294  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=9 kw_rank=7 dense=0.6877 kw=4.935
- 9. score 0.0288  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=8 kw_rank=11 dense=0.6905 kw=4.276
- 10. score 0.0286  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=12 kw_rank=8 dense=0.6554 kw=4.8092

---

## W12 - `ERR-4077`

**Question:** An invoice PDF will not render and reports ERR-4077. How do we resolve it?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4077

**Hit requires:** `ERR-4077`, `Regenerate PDF`

### dense -> HIT at rank 1

- 1. score 0.8445  `HC-4002-structured-006`  HC-4002  [ANSWER]
- 2. score 0.7398  `HC-4005-structured-004`  HC-4005
- 3. score 0.7201  `HC-4002-structured-004`  HC-4002
- 4. score 0.7148  `HC-4002-structured-003`  HC-4002
- 5. score 0.7003  `HC-4002-structured-005`  HC-4002
- 6. score 0.6737  `HC-4005-structured-003`  HC-4005
- 7. score 0.6658  `HC-4006-structured-004`  HC-4006
- 8. score 0.6584  `HC-4002-structured-007`  HC-4002
- 9. score 0.6541  `HC-4001-structured-006`  HC-4001
- 10. score 0.6455  `HC-4002-structured-002`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4002-structured-006`  HC-4002  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8445 kw=17.5651
- 2. score 0.0317  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=3 kw_rank=3 dense=0.7201 kw=7.2632
- 3. score 0.0310  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=5 kw_rank=4 dense=0.7003 kw=7.2603
- 4. score 0.0306  `HC-4002-structured-003`  HC-4002  [both]  dense_rank=4 kw_rank=7 dense=0.7148 kw=6.2109
- 5. score 0.0296  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=14 dense=0.7398 kw=4.5901
- 6. score 0.0292  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=8 kw_rank=9 dense=0.6584 kw=5.6417
- 7. score 0.0291  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=13 kw_rank=5 dense=0.6302 kw=6.7051
- 8. score 0.0288  `HC-4006-structured-004`  HC-4006  [both]  dense_rank=7 kw_rank=12 dense=0.6658 kw=4.7742
- 9. score 0.0288  `HC-4001-structured-006`  HC-4001  [both]  dense_rank=9 kw_rank=10 dense=0.6541 kw=5.2648
- 10. score 0.0283  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=16 kw_rank=6 dense=0.6069 kw=6.3684

---

## W13 - `ERR-4090`

**Question:** An invoice has ERR-4090 and no ledger entry. Should we void it?

**Known-correct location:** `HC-4002` -> Invoice error codes -> ERR-4090

**Hit requires:** `ERR-4090`, `backfilled`

### dense -> HIT at rank 1

- 1. score 0.8197  `HC-4002-structured-006`  HC-4002  [ANSWER]
- 2. score 0.7774  `HC-4005-structured-004`  HC-4005
- 3. score 0.7665  `HC-4002-structured-007`  HC-4002
- 4. score 0.7606  `HC-4002-structured-005`  HC-4002
- 5. score 0.7480  `HC-4002-structured-004`  HC-4002
- 6. score 0.7007  `HC-4003-structured-005`  HC-4003
- 7. score 0.6977  `HC-4005-structured-003`  HC-4005
- 8. score 0.6937  `HC-4001-structured-002`  HC-4001
- 9. score 0.6856  `HC-4002-structured-002`  HC-4002
- 10. score 0.6830  `HC-4002-structured-001`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4002-structured-006`  HC-4002  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8197 kw=23.4213
- 2. score 0.0320  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=3 kw_rank=2 dense=0.7665 kw=13.3446
- 3. score 0.0318  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=4 dense=0.7774 kw=8.5336
- 4. score 0.0310  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=4 kw_rank=5 dense=0.7606 kw=7.7224
- 5. score 0.0299  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=5 kw_rank=9 dense=0.748 kw=6.7879
- 6. score 0.0296  `HC-4002-structured-002`  HC-4002  [both]  dense_rank=9 kw_rank=6 dense=0.6856 kw=7.2748
- 7. score 0.0296  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=8 kw_rank=7 dense=0.6937 kw=7.1451
- 8. score 0.0288  `HC-4006-structured-004`  HC-4006  [both]  dense_rank=11 kw_rank=8 dense=0.6821 kw=7.0934
- 9. score 0.0286  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=10 kw_rank=10 dense=0.683 kw=6.283
- 10. score 0.0285  `HC-4001-structured-001`  HC-4001  [both]  dense_rank=19 kw_rank=3 dense=0.6404 kw=9.831

---

## W14 - `ERR-5101`

**Question:** A card was declined with ERR-5101. How many times should we retry?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5101

**Hit requires:** `ERR-5101`, `fraud block`

### dense -> HIT at rank 1

- 1. score 0.7934  `HC-4003-structured-004`  HC-4003  [ANSWER]
- 2. score 0.7613  `HC-4003-structured-005`  HC-4003
- 3. score 0.7183  `HC-4002-structured-005`  HC-4002
- 4. score 0.7119  `HC-4003-structured-003`  HC-4003
- 5. score 0.7050  `HC-4004-structured-005`  HC-4004
- 6. score 0.6995  `HC-4006-structured-005`  HC-4006
- 7. score 0.6822  `HC-4003-structured-001`  HC-4003
- 8. score 0.6748  `HC-4005-structured-004`  HC-4005
- 9. score 0.6733  `HC-4002-structured-004`  HC-4002
- 10. score 0.6678  `HC-4005-structured-003`  HC-4005

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4003-structured-004`  HC-4003  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7934 kw=15.0163
- 2. score 0.0320  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=2 kw_rank=3 dense=0.7613 kw=7.6064
- 3. score 0.0311  `HC-4003-structured-001`  HC-4003  [both]  dense_rank=7 kw_rank=2 dense=0.6822 kw=7.9468
- 4. score 0.0308  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=5 kw_rank=5 dense=0.705 kw=6.5913
- 5. score 0.0294  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=10 kw_rank=6 dense=0.6678 kw=6.5601
- 6. score 0.0292  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=15 dense=0.7183 kw=2.4789
- 7. score 0.0290  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=11 kw_rank=7 dense=0.6658 kw=4.8952
- 8. score 0.0283  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=19 kw_rank=4 dense=0.6088 kw=7.3874
- 9. score 0.0281  `HC-4003-structured-003`  HC-4003  [both]  dense_rank=4 kw_rank=20 dense=0.7119 kw=1.8756
- 10. score 0.0278  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=15 kw_rank=9 dense=0.637 kw=4.0745

---

## W15 - `ERR-5108`

**Question:** A renewal failed with ERR-5108. What should the agent ask the customer to do?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5108

**Hit requires:** `ERR-5108`, `re-enter the card`

### dense -> MISS (answer at rank 4)

- 1. score 0.7485  `HC-4005-structured-004`  HC-4005
- 2. score 0.7408  `HC-4004-structured-005`  HC-4004
- 3. score 0.7389  `HC-4002-structured-005`  HC-4002
- 4. score 0.7387  `HC-4003-structured-004`  HC-4003  [ANSWER]
- 5. score 0.7232  `HC-4003-structured-005`  HC-4003
- 6. score 0.7203  `HC-4002-structured-004`  HC-4002
- 7. score 0.7041  `HC-4005-structured-003`  HC-4005
- 8. score 0.7019  `HC-4002-structured-006`  HC-4002
- 9. score 0.6926  `HC-4002-structured-007`  HC-4002
- 10. score 0.6785  `HC-4003-structured-003`  HC-4003

### hybrid -> HIT at rank 1

- 1. score 0.0320  `HC-4003-structured-004`  HC-4003  [ANSWER, both]  dense_rank=4 kw_rank=1 dense=0.7387 kw=16.4157
- 2. score 0.0313  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=1 kw_rank=7 dense=0.7485 kw=6.195
- 3. score 0.0311  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=7 kw_rank=2 dense=0.7041 kw=9.1001
- 4. score 0.0310  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=5 kw_rank=4 dense=0.7232 kw=8.072
- 5. score 0.0296  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=2 kw_rank=14 dense=0.7408 kw=4.8364
- 6. score 0.0296  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=13 dense=0.7389 kw=4.977
- 7. score 0.0294  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=6 kw_rank=10 dense=0.7203 kw=5.6902
- 8. score 0.0294  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=8 kw_rank=8 dense=0.7019 kw=6.0494
- 9. score 0.0293  `HC-4001-structured-005`  HC-4001  [both]  dense_rank=12 kw_rank=5 dense=0.6722 kw=7.7561
- 10. score 0.0282  `HC-4004-structured-004`  HC-4004  [both]  dense_rank=11 kw_rank=11 dense=0.6741 kw=5.4506

---

## W16 - `ERR-5114`

**Question:** What does ERR-5114 mean, and do we need to retry the payment manually?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5114

**Hit requires:** `ERR-5114`, `dunning schedule will retry`

### dense -> HIT at rank 3

- 1. score 0.8102  `HC-4003-structured-005`  HC-4003
- 2. score 0.7681  `HC-4002-structured-005`  HC-4002
- 3. score 0.7588  `HC-4003-structured-004`  HC-4003  [ANSWER]
- 4. score 0.7411  `HC-4004-structured-005`  HC-4004
- 5. score 0.7255  `HC-4005-structured-004`  HC-4005
- 6. score 0.7191  `HC-4002-structured-006`  HC-4002
- 7. score 0.7186  `HC-4002-structured-004`  HC-4002
- 8. score 0.7109  `HC-4005-structured-003`  HC-4005
- 9. score 0.7090  `HC-4001-structured-002`  HC-4001
- 10. score 0.7068  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0323  `HC-4003-structured-004`  HC-4003  [ANSWER, both]  dense_rank=3 kw_rank=1 dense=0.7588 kw=12.7788
- 2. score 0.0323  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=1 kw_rank=3 dense=0.8102 kw=8.1684
- 3. score 0.0312  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=4 kw_rank=4 dense=0.7411 kw=7.3115
- 4. score 0.0308  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=8 dense=0.7681 kw=5.3705
- 5. score 0.0299  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=8 kw_rank=6 dense=0.7109 kw=5.9725
- 6. score 0.0292  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=6 kw_rank=11 dense=0.7191 kw=4.1469
- 7. score 0.0291  `HC-4003-structured-001`  HC-4003  [both]  dense_rank=17 kw_rank=2 dense=0.6488 kw=10.6598
- 8. score 0.0288  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=10 kw_rank=9 dense=0.7068 kw=5.3704
- 9. score 0.0285  `HC-4004-structured-004`  HC-4004  [both]  dense_rank=16 kw_rank=5 dense=0.6527 kw=6.0569
- 10. score 0.0285  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=5 kw_rank=16 dense=0.7255 kw=3.4567

---

## W17 - `ERR-5127`

**Question:** A payment failed with ERR-5127 after 3-D Secure. How long is the new link valid?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5127

**Hit requires:** `ERR-5127`, `Links expire after 30 minutes`

### dense -> HIT at rank 2

- 1. score 0.7391  `HC-4003-structured-005`  HC-4003
- 2. score 0.7118  `HC-4003-structured-004`  HC-4003  [ANSWER]
- 3. score 0.7039  `HC-4002-structured-005`  HC-4002
- 4. score 0.7029  `HC-4001-structured-002`  HC-4001
- 5. score 0.7019  `HC-4004-structured-005`  HC-4004
- 6. score 0.7016  `HC-4002-structured-006`  HC-4002
- 7. score 0.6877  `HC-4006-structured-005`  HC-4006
- 8. score 0.6746  `HC-4002-structured-004`  HC-4002
- 9. score 0.6715  `HC-4005-structured-003`  HC-4005
- 10. score 0.6693  `HC-4006-structured-004`  HC-4006

### hybrid -> HIT at rank 1

- 1. score 0.0325  `HC-4003-structured-004`  HC-4003  [ANSWER, both]  dense_rank=2 kw_rank=1 dense=0.7118 kw=25.3645
- 2. score 0.0315  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=1 kw_rank=6 dense=0.7391 kw=5.8525
- 3. score 0.0313  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=6 kw_rank=2 dense=0.7016 kw=8.5167
- 4. score 0.0303  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=5 kw_rank=7 dense=0.7019 kw=5.7396
- 5. score 0.0301  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=9 kw_rank=4 dense=0.6715 kw=7.6307
- 6. score 0.0290  `HC-4006-structured-005`  HC-4006  [both]  dense_rank=7 kw_rank=11 dense=0.6877 kw=4.554
- 7. score 0.0290  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=4 kw_rank=15 dense=0.7029 kw=3.502
- 8. score 0.0289  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=17 dense=0.7039 kw=2.9367
- 9. score 0.0288  `HC-4006-structured-004`  HC-4006  [both]  dense_rank=10 kw_rank=9 dense=0.6693 kw=5.1322
- 10. score 0.0286  `HC-4003-structured-003`  HC-4003  [both]  dense_rank=12 kw_rank=8 dense=0.6554 kw=5.4638

---

## W18 - `ERR-5133`

**Question:** A valid card is failing with ERR-5133. What is mismatched and how do we fix it?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5133

**Hit requires:** `ERR-5133`, `account tax country`

### dense -> HIT at rank 1

- 1. score 0.8248  `HC-4003-structured-005`  HC-4003  [ANSWER]
- 2. score 0.7427  `HC-4002-structured-005`  HC-4002
- 3. score 0.7187  `HC-4003-structured-004`  HC-4003
- 4. score 0.7186  `HC-4002-structured-006`  HC-4002
- 5. score 0.7053  `HC-4004-structured-005`  HC-4004
- 6. score 0.7030  `HC-4002-structured-004`  HC-4002
- 7. score 0.6968  `HC-4005-structured-003`  HC-4005
- 8. score 0.6854  `HC-4005-structured-004`  HC-4005
- 9. score 0.6396  `HC-4001-structured-005`  HC-4001
- 10. score 0.6389  `HC-4001-structured-002`  HC-4001

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4003-structured-005`  HC-4003  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8248 kw=16.8426
- 2. score 0.0317  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=3 kw_rank=3 dense=0.7187 kw=9.2114
- 3. score 0.0312  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=4 kw_rank=4 dense=0.7186 kw=9.119
- 4. score 0.0308  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=8 dense=0.7427 kw=5.992
- 5. score 0.0303  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=7 kw_rank=5 dense=0.6968 kw=7.6999
- 6. score 0.0299  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=5 kw_rank=9 dense=0.7053 kw=5.9781
- 7. score 0.0296  `HC-4003-structured-001`  HC-4003  [both]  dense_rank=14 kw_rank=2 dense=0.6146 kw=10.9484
- 8. score 0.0287  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=6 kw_rank=14 dense=0.703 kw=4.6803
- 9. score 0.0284  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=8 kw_rank=13 dense=0.6854 kw=4.8404
- 10. score 0.0283  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=16 kw_rank=6 dense=0.6121 kw=7.3713

---

## W19 - `ERR-5140`

**Question:** A wallet payment is failing with ERR-5140. What are the customer's options?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5140

**Hit requires:** `ERR-5140`, `original device`

### dense -> HIT at rank 1

- 1. score 0.8372  `HC-4003-structured-005`  HC-4003  [ANSWER]
- 2. score 0.7467  `HC-4002-structured-005`  HC-4002
- 3. score 0.7247  `HC-4002-structured-006`  HC-4002
- 4. score 0.7219  `HC-4003-structured-004`  HC-4003
- 5. score 0.7054  `HC-4004-structured-005`  HC-4004
- 6. score 0.6844  `HC-4002-structured-004`  HC-4002
- 7. score 0.6827  `HC-4005-structured-003`  HC-4005
- 8. score 0.6796  `HC-4005-structured-004`  HC-4005
- 9. score 0.6705  `HC-4001-structured-002`  HC-4001
- 10. score 0.6657  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4003-structured-005`  HC-4003  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8372 kw=13.6923
- 2. score 0.0315  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=5 kw_rank=2 dense=0.7054 kw=8.6505
- 3. score 0.0308  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=4 kw_rank=6 dense=0.7219 kw=5.8041
- 4. score 0.0306  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=7 kw_rank=4 dense=0.6827 kw=7.1518
- 5. score 0.0293  `HC-4006-structured-005`  HC-4006  [both]  dense_rank=12 kw_rank=5 dense=0.6507 kw=6.2659
- 6. score 0.0289  `HC-4003-structured-002`  HC-4003  [both]  dense_rank=17 kw_rank=3 dense=0.6065 kw=8.18
- 7. score 0.0288  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=19 dense=0.7467 kw=3.4786
- 8. score 0.0288  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=10 kw_rank=9 dense=0.6657 kw=4.3722
- 9. score 0.0279  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=8 kw_rank=16 dense=0.6796 kw=3.5724
- 10. score 0.0277  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=6 kw_rank=20 dense=0.6844 kw=3.4769

---

## W20 - `ERR-5199`

**Question:** We got ERR-5199 from the processor. Should the agent retry the charge?

**Known-correct location:** `HC-4003` -> Decline and token error codes -> ERR-5199

**Hit requires:** `ERR-5199`, `Escalate to Payments Ops`

### dense -> HIT at rank 1

- 1. score 0.7573  `HC-4003-structured-005`  HC-4003  [ANSWER]
- 2. score 0.7433  `HC-4002-structured-005`  HC-4002
- 3. score 0.7194  `HC-4004-structured-005`  HC-4004
- 4. score 0.6941  `HC-4005-structured-004`  HC-4005
- 5. score 0.6886  `HC-4003-structured-004`  HC-4003
- 6. score 0.6869  `HC-4001-structured-002`  HC-4001
- 7. score 0.6862  `HC-4002-structured-006`  HC-4002
- 8. score 0.6827  `HC-4002-structured-004`  HC-4002
- 9. score 0.6812  `HC-4002-structured-007`  HC-4002
- 10. score 0.6612  `HC-4005-structured-003`  HC-4005

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4003-structured-005`  HC-4003  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7573 kw=14.036
- 2. score 0.0315  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=5 kw_rank=2 dense=0.6886 kw=6.2362
- 3. score 0.0313  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=3 kw_rank=5 dense=0.7194 kw=4.7313
- 4. score 0.0299  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=4 kw_rank=10 dense=0.6941 kw=3.8123
- 5. score 0.0298  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=13 dense=0.7433 kw=2.9736
- 6. score 0.0289  `HC-4003-structured-001`  HC-4003  [both]  dense_rank=17 kw_rank=3 dense=0.616 kw=5.9488
- 7. score 0.0288  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=10 kw_rank=9 dense=0.6612 kw=4.2737
- 8. score 0.0283  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=7 kw_rank=15 dense=0.6862 kw=2.8318
- 9. score 0.0282  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=8 kw_rank=14 dense=0.6827 kw=2.9247
- 10. score 0.0282  `HC-4001-structured-005`  HC-4001  [both]  dense_rank=11 kw_rank=11 dense=0.6598 kw=3.5611

---

## W21 - `ERR-6203`

**Question:** A plan change was rejected with ERR-6203. What is the cause and the fix?

**Known-correct location:** `HC-4004` -> Plan change errors -> ERR-6203

**Hit requires:** `ERR-6203`, `higher seat count`

### dense -> HIT at rank 1

- 1. score 0.8322  `HC-4004-structured-005`  HC-4004  [ANSWER]
- 2. score 0.6921  `HC-4006-structured-002`  HC-4006
- 3. score 0.6919  `HC-4002-structured-006`  HC-4002
- 4. score 0.6893  `HC-4003-structured-004`  HC-4003
- 5. score 0.6888  `HC-4002-structured-004`  HC-4002
- 6. score 0.6872  `HC-4002-structured-005`  HC-4002
- 7. score 0.6706  `HC-4003-structured-005`  HC-4003
- 8. score 0.6675  `HC-4006-structured-004`  HC-4006
- 9. score 0.6670  `HC-4001-structured-002`  HC-4001
- 10. score 0.6599  `HC-4005-structured-003`  HC-4005

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4004-structured-005`  HC-4004  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8322 kw=19.2575
- 2. score 0.0315  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=4 kw_rank=3 dense=0.6893 kw=8.0934
- 3. score 0.0311  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=7 kw_rank=2 dense=0.6706 kw=9.1224
- 4. score 0.0310  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=3 kw_rank=6 dense=0.6919 kw=7.8908
- 5. score 0.0305  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=6 kw_rank=5 dense=0.6872 kw=7.9661
- 6. score 0.0299  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=10 kw_rank=4 dense=0.6599 kw=8.084
- 7. score 0.0293  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=5 kw_rank=12 dense=0.6888 kw=5.3926
- 8. score 0.0291  `HC-4006-structured-002`  HC-4006  [both]  dense_rank=2 kw_rank=17 dense=0.6921 kw=3.4536
- 9. score 0.0290  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=9 kw_rank=9 dense=0.667 kw=6.3375
- 10. score 0.0288  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=11 kw_rank=8 dense=0.6545 kw=6.5556

---

## W22 - `ERR-6210`

**Question:** A customer cannot change plan and sees ERR-6210. Who handles it?

**Known-correct location:** `HC-4004` -> Plan change errors -> ERR-6210

**Hit requires:** `ERR-6210`, `Route to the account manager`

### dense -> HIT at rank 1

- 1. score 0.7955  `HC-4004-structured-005`  HC-4004  [ANSWER]
- 2. score 0.7090  `HC-4002-structured-005`  HC-4002
- 3. score 0.6925  `HC-4002-structured-006`  HC-4002
- 4. score 0.6899  `HC-4002-structured-004`  HC-4002
- 5. score 0.6858  `HC-4003-structured-005`  HC-4003
- 6. score 0.6737  `HC-4005-structured-004`  HC-4005
- 7. score 0.6664  `HC-4001-structured-002`  HC-4001
- 8. score 0.6637  `HC-4003-structured-004`  HC-4003
- 9. score 0.6616  `HC-4006-structured-002`  HC-4006
- 10. score 0.6538  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4004-structured-005`  HC-4004  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7955 kw=16.0636
- 2. score 0.0320  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=3 dense=0.709 kw=6.2503
- 3. score 0.0311  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=7 kw_rank=2 dense=0.6664 kw=6.7435
- 4. score 0.0300  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=3 kw_rank=11 dense=0.6925 kw=4.1731
- 5. score 0.0299  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=4 kw_rank=10 dense=0.6899 kw=4.1768
- 6. score 0.0297  `HC-4001-structured-005`  HC-4001  [both]  dense_rank=11 kw_rank=4 dense=0.6516 kw=5.8401
- 7. score 0.0292  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=8 kw_rank=9 dense=0.6637 kw=4.6975
- 8. score 0.0284  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=5 kw_rank=17 dense=0.6858 kw=3.4225
- 9. score 0.0283  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=6 kw_rank=16 dense=0.6737 kw=3.4589
- 10. score 0.0280  `HC-4006-structured-005`  HC-4006  [both]  dense_rank=18 kw_rank=6 dense=0.5996 kw=5.6275

---

## W23 - `ERR-6244`

**Question:** What causes ERR-6244 on a plan change, and what should we wait for?

**Known-correct location:** `HC-4004` -> Plan change errors -> ERR-6244

**Hit requires:** `ERR-6244`, `hourly finalisation run`

### dense -> HIT at rank 1

- 1. score 0.8281  `HC-4004-structured-005`  HC-4004  [ANSWER]
- 2. score 0.7144  `HC-4002-structured-005`  HC-4002
- 3. score 0.7098  `HC-4006-structured-002`  HC-4006
- 4. score 0.7015  `HC-4003-structured-004`  HC-4003
- 5. score 0.6973  `HC-4002-structured-004`  HC-4002
- 6. score 0.6967  `HC-4001-structured-002`  HC-4001
- 7. score 0.6840  `HC-4002-structured-006`  HC-4002
- 8. score 0.6784  `HC-4001-structured-005`  HC-4001
- 9. score 0.6727  `HC-4006-structured-004`  HC-4006
- 10. score 0.6677  `HC-4005-structured-004`  HC-4005

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4004-structured-005`  HC-4004  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8281 kw=18.063
- 2. score 0.0308  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=8 dense=0.7144 kw=5.3409
- 3. score 0.0303  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=6 kw_rank=6 dense=0.6967 kw=6.2372
- 4. score 0.0294  `HC-4006-structured-002`  HC-4006  [both]  dense_rank=3 kw_rank=14 dense=0.7098 kw=3.9913
- 5. score 0.0287  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=5 kw_rank=15 dense=0.6973 kw=3.9906
- 6. score 0.0286  `HC-4001-structured-005`  HC-4001  [both]  dense_rank=8 kw_rank=12 dense=0.6784 kw=4.5836
- 7. score 0.0284  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=18 kw_rank=4 dense=0.6319 kw=7.7736
- 8. score 0.0281  `HC-4006-structured-001`  HC-4006  [both]  dense_rank=16 kw_rank=7 dense=0.6399 kw=5.6591
- 9. score 0.0278  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=11 kw_rank=13 dense=0.6621 kw=4.2812
- 10. score 0.0274  `HC-4001-structured-003`  HC-4001  [both]  dense_rank=15 kw_rank=11 dense=0.6422 kw=4.587

---

## W24 - `ERR-6250`

**Question:** A plan change is blocked with ERR-6250. What has to happen first?

**Known-correct location:** `HC-4004` -> Plan change errors -> ERR-6250

**Hit requires:** `ERR-6250`, `Collect payment first`

### dense -> HIT at rank 1

- 1. score 0.8333  `HC-4004-structured-005`  HC-4004  [ANSWER]
- 2. score 0.6945  `HC-4001-structured-002`  HC-4001
- 3. score 0.6940  `HC-4006-structured-002`  HC-4006
- 4. score 0.6816  `HC-4003-structured-004`  HC-4003
- 5. score 0.6771  `HC-4002-structured-006`  HC-4002
- 6. score 0.6767  `HC-4002-structured-005`  HC-4002
- 7. score 0.6678  `HC-4006-structured-004`  HC-4006
- 8. score 0.6620  `HC-4001-structured-005`  HC-4001
- 9. score 0.6587  `HC-4003-structured-005`  HC-4003
- 10. score 0.6577  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4004-structured-005`  HC-4004  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8333 kw=20.681
- 2. score 0.0311  `HC-4001-structured-002`  HC-4001  [both]  dense_rank=2 kw_rank=7 dense=0.6945 kw=5.626
- 3. score 0.0306  `HC-4001-structured-005`  HC-4001  [both]  dense_rank=8 kw_rank=3 dense=0.662 kw=8.074
- 4. score 0.0303  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=6 kw_rank=6 dense=0.6767 kw=6.1151
- 5. score 0.0295  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=5 kw_rank=11 dense=0.6771 kw=4.7066
- 6. score 0.0295  `HC-4004-structured-002`  HC-4004  [both]  dense_rank=15 kw_rank=2 dense=0.6413 kw=8.7832
- 7. score 0.0294  `HC-4006-structured-002`  HC-4006  [both]  dense_rank=3 kw_rank=14 dense=0.694 kw=4.1663
- 8. score 0.0293  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=4 kw_rank=13 dense=0.6816 kw=4.4013
- 9. score 0.0293  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=12 kw_rank=5 dense=0.6499 kw=6.1369
- 10. score 0.0288  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=10 kw_rank=9 dense=0.6577 kw=5.1687

---

## W25 - `ERR-7101`

**Question:** A tax ID was rejected with ERR-7101. What is usually wrong with it?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> ERR-7101

**Hit requires:** `ERR-7101`, `Correct the format on the Tax tab`

### dense -> HIT at rank 1

- 1. score 0.7840  `HC-4005-structured-003`  HC-4005  [ANSWER]
- 2. score 0.7564  `HC-4005-structured-004`  HC-4005
- 3. score 0.7529  `HC-4003-structured-005`  HC-4003
- 4. score 0.7391  `HC-4005-structured-001`  HC-4005
- 5. score 0.7271  `HC-4005-structured-002`  HC-4005
- 6. score 0.7240  `HC-4002-structured-004`  HC-4002
- 7. score 0.7149  `HC-4003-structured-004`  HC-4003
- 8. score 0.7054  `HC-4002-structured-005`  HC-4002
- 9. score 0.7015  `HC-4004-structured-005`  HC-4004
- 10. score 0.6940  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4005-structured-003`  HC-4005  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.784 kw=21.6556
- 2. score 0.0318  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=4 kw_rank=2 dense=0.7391 kw=11.4744
- 3. score 0.0315  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=3 kw_rank=4 dense=0.7529 kw=7.5354
- 4. score 0.0303  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=7 kw_rank=5 dense=0.7149 kw=7.0495
- 5. score 0.0300  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=12 dense=0.7564 kw=4.8297
- 6. score 0.0296  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=9 kw_rank=6 dense=0.7015 kw=6.4793
- 7. score 0.0294  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=6 kw_rank=10 dense=0.724 kw=5.1523
- 8. score 0.0294  `HC-4001-structured-005`  HC-4001  [both]  dense_rank=14 kw_rank=3 dense=0.6348 kw=7.6173
- 9. score 0.0291  `HC-4005-structured-002`  HC-4005  [both]  dense_rank=5 kw_rank=13 dense=0.7271 kw=4.6361
- 10. score 0.0290  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=11 kw_rank=7 dense=0.693 kw=5.7996

---

## W26 - `ERR-7203`

**Question:** A VAT number is failing with ERR-7203. What causes it and how do we clear it?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> ERR-7203

**Hit requires:** `ERR-7203`, `Revalidate on the Tax tab`

### dense -> HIT at rank 1

- 1. score 0.8057  `HC-4005-structured-003`  HC-4005  [ANSWER]
- 2. score 0.7715  `HC-4005-structured-004`  HC-4005
- 3. score 0.7660  `HC-4002-structured-005`  HC-4002
- 4. score 0.7578  `HC-4002-structured-004`  HC-4002
- 5. score 0.7462  `HC-4005-structured-001`  HC-4005
- 6. score 0.7273  `HC-4002-structured-006`  HC-4002
- 7. score 0.7229  `HC-4003-structured-005`  HC-4003
- 8. score 0.7195  `HC-4004-structured-005`  HC-4004
- 9. score 0.7021  `HC-4003-structured-004`  HC-4003
- 10. score 0.6954  `HC-4005-structured-002`  HC-4005

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4005-structured-003`  HC-4005  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8057 kw=14.3186
- 2. score 0.0315  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=5 kw_rank=2 dense=0.7462 kw=12.454
- 3. score 0.0303  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=6 kw_rank=6 dense=0.7273 kw=8.1717
- 4. score 0.0300  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=11 kw_rank=3 dense=0.6763 kw=9.86
- 5. score 0.0288  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=4 kw_rank=16 dense=0.7578 kw=4.3313
- 6. score 0.0288  `HC-4005-structured-005`  HC-4005  [both]  dense_rank=16 kw_rank=4 dense=0.651 kw=9.2827
- 7. score 0.0288  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=9 kw_rank=10 dense=0.7021 kw=6.483
- 8. score 0.0285  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=19 dense=0.766 kw=3.8589
- 9. score 0.0280  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=15 kw_rank=8 dense=0.653 kw=6.6641
- 10. score 0.0280  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=8 kw_rank=15 dense=0.7195 kw=4.414

---

## W27 - `ERR-7208`

**Question:** What does ERR-7208 mean, and should we remove the customer's VAT ID?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> ERR-7208

**Hit requires:** `ERR-7208`, `Retry after one hour`

### dense -> HIT at rank 1

- 1. score 0.7827  `HC-4005-structured-003`  HC-4005  [ANSWER]
- 2. score 0.7569  `HC-4005-structured-004`  HC-4005
- 3. score 0.7514  `HC-4002-structured-004`  HC-4002
- 4. score 0.7460  `HC-4002-structured-005`  HC-4002
- 5. score 0.7402  `HC-4005-structured-001`  HC-4005
- 6. score 0.7147  `HC-4004-structured-005`  HC-4004
- 7. score 0.7127  `HC-4003-structured-005`  HC-4003
- 8. score 0.7038  `HC-4002-structured-006`  HC-4002
- 9. score 0.6984  `HC-4003-structured-004`  HC-4003
- 10. score 0.6975  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4005-structured-003`  HC-4005  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7827 kw=19.326
- 2. score 0.0315  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=5 kw_rank=2 dense=0.7402 kw=9.8788
- 3. score 0.0310  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=6 kw_rank=3 dense=0.7147 kw=8.3319
- 4. score 0.0299  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=4 kw_rank=10 dense=0.746 kw=4.4325
- 5. score 0.0299  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=8 kw_rank=6 dense=0.7038 kw=5.1463
- 6. score 0.0297  `HC-4005-structured-002`  HC-4005  [both]  dense_rank=11 kw_rank=4 dense=0.6948 kw=6.2555
- 7. score 0.0296  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=2 kw_rank=14 dense=0.7569 kw=3.4323
- 8. score 0.0294  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=7 kw_rank=9 dense=0.7127 kw=4.6018
- 9. score 0.0292  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=3 kw_rank=15 dense=0.7514 kw=3.2381
- 10. score 0.0284  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=9 kw_rank=12 dense=0.6984 kw=3.8778

---

## W28 - `ERR-7215`

**Question:** A VAT ID check returns ERR-7215. What do we need to change on the account?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> ERR-7215

**Hit requires:** `ERR-7215`, `legal entity name`

### dense -> HIT at rank 1

- 1. score 0.7941  `HC-4005-structured-003`  HC-4005  [ANSWER]
- 2. score 0.7874  `HC-4005-structured-001`  HC-4005
- 3. score 0.7445  `HC-4002-structured-005`  HC-4002
- 4. score 0.7372  `HC-4005-structured-004`  HC-4005
- 5. score 0.7361  `HC-4002-structured-004`  HC-4002
- 6. score 0.7321  `HC-4005-structured-002`  HC-4005
- 7. score 0.7269  `HC-4004-structured-005`  HC-4004
- 8. score 0.7233  `HC-4003-structured-005`  HC-4003
- 9. score 0.6881  `HC-4002-structured-006`  HC-4002
- 10. score 0.6865  `HC-4002-structured-007`  HC-4002

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4005-structured-003`  HC-4005  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7941 kw=17.1269
- 2. score 0.0315  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=2 kw_rank=5 dense=0.7874 kw=9.0982
- 3. score 0.0313  `HC-4005-structured-002`  HC-4005  [both]  dense_rank=6 kw_rank=2 dense=0.7321 kw=10.3629
- 4. score 0.0306  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=3 kw_rank=8 dense=0.7445 kw=7.191
- 5. score 0.0294  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=7 kw_rank=9 dense=0.7269 kw=7.0446
- 6. score 0.0290  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=8 kw_rank=10 dense=0.7233 kw=6.4022
- 7. score 0.0286  `HC-4005-structured-004`  HC-4005  [both]  dense_rank=4 kw_rank=17 dense=0.7372 kw=3.9926
- 8. score 0.0285  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=5 kw_rank=16 dense=0.7361 kw=4.1292
- 9. score 0.0284  `HC-4006-structured-002`  HC-4006  [both]  dense_rank=18 kw_rank=4 dense=0.6437 kw=9.2791
- 10. score 0.0278  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=9 kw_rank=15 dense=0.6881 kw=4.1311

---

## W29 - `ERR-7302`

**Question:** An invoice line item reports ERR-7302. What is missing and how do we fix it?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> ERR-7302

**Hit requires:** `ERR-7302`, `Set a tax code on the product`

### dense -> HIT at rank 1

- 1. score 0.8101  `HC-4005-structured-004`  HC-4005  [ANSWER]
- 2. score 0.8101  `HC-4002-structured-006`  HC-4002
- 3. score 0.7851  `HC-4002-structured-004`  HC-4002
- 4. score 0.7712  `HC-4002-structured-005`  HC-4002
- 5. score 0.7192  `HC-4004-structured-005`  HC-4004
- 6. score 0.7114  `HC-4005-structured-003`  HC-4005
- 7. score 0.7096  `HC-4002-structured-003`  HC-4002
- 8. score 0.6936  `HC-4002-structured-007`  HC-4002
- 9. score 0.6929  `HC-4006-structured-002`  HC-4006
- 10. score 0.6892  `HC-4003-structured-005`  HC-4003

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4005-structured-004`  HC-4005  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.8101 kw=17.5858
- 2. score 0.0323  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=2 kw_rank=2 dense=0.8101 kw=14.2129
- 3. score 0.0317  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=3 kw_rank=3 dense=0.7851 kw=13.2372
- 4. score 0.0306  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=4 kw_rank=7 dense=0.7712 kw=7.4104
- 5. score 0.0294  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=8 kw_rank=8 dense=0.6936 kw=7.2318
- 6. score 0.0293  `HC-4001-structured-006`  HC-4001  [both]  dense_rank=13 kw_rank=4 dense=0.6754 kw=8.5075
- 7. score 0.0290  `HC-4002-structured-001`  HC-4002  [both]  dense_rank=12 kw_rank=6 dense=0.6851 kw=7.4574
- 8. score 0.0289  `HC-4004-structured-005`  HC-4004  [both]  dense_rank=5 kw_rank=14 dense=0.7192 kw=5.5091
- 9. score 0.0283  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=6 kw_rank=16 dense=0.7114 kw=4.744
- 10. score 0.0280  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=19 kw_rank=5 dense=0.6402 kw=8.1877

---

## W30 - `ERR-7310`

**Question:** A US customer is being charged tax and we see ERR-7310. What do we ask for?

**Known-correct location:** `HC-4005` -> Tax validation error codes -> ERR-7310

**Hit requires:** `ERR-7310`, `upload a current certificate`

### dense -> HIT at rank 1

- 1. score 0.7901  `HC-4005-structured-004`  HC-4005  [ANSWER]
- 2. score 0.7522  `HC-4002-structured-005`  HC-4002
- 3. score 0.7446  `HC-4002-structured-004`  HC-4002
- 4. score 0.7437  `HC-4003-structured-005`  HC-4003
- 5. score 0.7193  `HC-4005-structured-003`  HC-4005
- 6. score 0.7088  `HC-4002-structured-006`  HC-4002
- 7. score 0.6945  `HC-4005-structured-001`  HC-4005
- 8. score 0.6798  `HC-4002-structured-007`  HC-4002
- 9. score 0.6736  `HC-4005-structured-005`  HC-4005
- 10. score 0.6694  `HC-4004-structured-005`  HC-4004

### hybrid -> HIT at rank 1

- 1. score 0.0328  `HC-4005-structured-004`  HC-4005  [ANSWER, both]  dense_rank=1 kw_rank=1 dense=0.7901 kw=17.0669
- 2. score 0.0312  `HC-4003-structured-005`  HC-4003  [both]  dense_rank=4 kw_rank=4 dense=0.7437 kw=9.3212
- 3. score 0.0308  `HC-4002-structured-005`  HC-4002  [both]  dense_rank=2 kw_rank=8 dense=0.7522 kw=6.8121
- 4. score 0.0305  `HC-4005-structured-003`  HC-4005  [both]  dense_rank=5 kw_rank=6 dense=0.7193 kw=8.5431
- 5. score 0.0303  `HC-4005-structured-001`  HC-4005  [both]  dense_rank=7 kw_rank=5 dense=0.6945 kw=8.7399
- 6. score 0.0298  `HC-4002-structured-004`  HC-4002  [both]  dense_rank=3 kw_rank=12 dense=0.7446 kw=5.6783
- 7. score 0.0290  `HC-4003-structured-004`  HC-4003  [both]  dense_rank=11 kw_rank=7 dense=0.6552 kw=6.8367
- 8. score 0.0290  `HC-4002-structured-007`  HC-4002  [both]  dense_rank=8 kw_rank=10 dense=0.6798 kw=5.7129
- 9. score 0.0290  `HC-4005-structured-005`  HC-4005  [both]  dense_rank=9 kw_rank=9 dense=0.6736 kw=6.0509
- 10. score 0.0280  `HC-4002-structured-006`  HC-4002  [both]  dense_rank=6 kw_rank=18 dense=0.7088 kw=3.7995
