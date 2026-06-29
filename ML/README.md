# KINORA Machine Learning Pipeline

This directory contains the complete training pipeline for **KINORA**, a content-based movie recommendation system built using a **Two-Tower Neural Network** with TensorFlow.

## Dataset

The MovieLens dataset is **not included** in this repository due to its large size.

Download the official **MovieLens 32M** dataset from:

https://grouplens.org/datasets/movielens/

After downloading, create a folder named `data` inside this directory and place the following files:

```text
data/
├── movies.csv
└── ratings.csv
```

The notebook automatically samples **5 million ratings** from the original dataset during preprocessing.

---

## Project Structure

```text
ML/
├── data/                     # Place MovieLens dataset here
├── Model/                    # Saved models and preprocessing objects
└── ContentBased_final.ipynb  # Complete training pipeline
```

---

## Workflow

The notebook covers the complete machine learning pipeline:

1. Data Loading
2. Data Preprocessing
3. Feature Engineering
4. User & Movie Feature Construction
5. Two-Tower Neural Network
6. Model Training
7. Model Evaluation
8. Embedding Generation
9. Recommendation Inference
10. Model Export for Deployment

---

## Model Performance

Evaluation on the held-out test set produced the following results:

| Metric | Value |
|--------|------:|
| Validation Loss (MSE) | **0.0310** |
| RMSE | **0.7922** |
| MAE | **0.6112** |

---

## Deployment

The trained User Tower, Movie Tower, preprocessing objects, and feature metadata are exported after training and are directly integrated into the KINORA Flask web application to generate real-time personalized movie recommendations.
=======