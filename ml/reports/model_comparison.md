# Old vs new model

## HAM10000 test (1502 images)

|                            |   old (HAM only) |   new (HAM + ISIC) |   change |
|:---------------------------|-----------------:|-------------------:|---------:|
| accuracy                   |            0.814 |              0.842 |    0.028 |
| balanced_accuracy          |            0.722 |              0.764 |    0.042 |
| macro_f1                   |            0.691 |              0.749 |    0.058 |
| recall_akiec               |            0.827 |              0.827 |    0     |
| recall_bcc                 |            0.817 |              0.915 |    0.098 |
| recall_bkl                 |            0.467 |              0.581 |    0.114 |
| recall_df                  |            0.75  |              0.7   |   -0.05  |
| recall_mel                 |            0.623 |              0.593 |   -0.03  |
| recall_nv                  |            0.906 |              0.925 |    0.019 |
| recall_vasc                |            0.667 |              0.81  |    0.143 |
| melanoma_flagged_high      |            0.766 |              0.784 |    0.018 |
| malignant_moderate_or_high |            0.89  |              0.931 |    0.041 |
| benign_flagged_high        |            0.157 |              0.146 |   -0.011 |


## Full new test (3703 images)

|                            |   old (HAM only) |   new (HAM + ISIC) |   change |
|:---------------------------|-----------------:|-------------------:|---------:|
| accuracy                   |            0.622 |              0.739 |    0.117 |
| balanced_accuracy          |            0.542 |              0.656 |    0.114 |
| macro_f1                   |            0.465 |              0.636 |    0.171 |
| recall_akiec               |            0.411 |              0.517 |    0.106 |
| recall_bcc                 |            0.327 |              0.82  |    0.493 |
| recall_bkl                 |            0.49  |              0.495 |    0.005 |
| recall_df                  |            0.676 |              0.514 |   -0.162 |
| recall_mel                 |            0.31  |              0.549 |    0.239 |
| recall_nv                  |            0.863 |              0.866 |    0.003 |
| recall_vasc                |            0.714 |              0.829 |    0.115 |
| melanoma_flagged_high      |            0.417 |              0.74  |    0.323 |
| malignant_moderate_or_high |            0.657 |              0.916 |    0.259 |
| benign_flagged_high        |            0.124 |              0.186 |    0.062 |

