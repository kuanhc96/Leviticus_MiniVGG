from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from imutils import paths
from sklearn.model_selection import train_test_split, RandomizedSearchCV, RepeatedKFold
from sklearn.metrics import classification_report

from toolbox.tf.nn.conv.miniVGGNet import MiniVGGNet
from toolbox.tf.loading.simple_dataset_loader import SimpleDatasetLoader
from toolbox.tf.preprocessing.simple_preprocessor import SimplePreprocessor
from config import PKL_PATH

import numpy as np
import os


app = FastAPI()


class MiniVGGTrainRequest(BaseModel):
    # this is a value auto-generated by the master node
    # It represents the ID of the current training job
    taskId: str 
    # This value will determite if a testing set is needed to be set aside 
    # for scoring. By default it is False, which means a test set should 
    # be set aside for scoring
    trainOnly: Optional[bool] = False
    # This is a string that represents the path to the training data
    dataset: str

class MiniVGGTrainResponse(BaseModel):
    # This is the same taskId that was sent to this container by the master node
    taskId: str
    # This is the path to which the pickled model is saved
    modelPath: str
    # This is the score representing the model's performance
    accuracy: float
    # This is a long string representing the classification report 
    # of the resulting model
    classificationReport: str

@app.post("/train")
def train(request: MiniVGGTrainRequest) -> dict:
    print("[INFO] Received MiniVGG Training Request")
    # initialize the local binary patterns descriptor along with the data and label lists
    dataset = request.dataset
    print(f"[INFO] Dataset Received For Training: {dataset.split(os.path.sep)[-1]}")
    taskId = request.taskId
    trainOnly = request.trainOnly

    trainX = []
    testX = []

    trainLabels = []
    testLabels = []

    predictions = []

    imagePaths = list(paths.list_images(dataset))
    preprocessor = SimplePreprocessor(256, 256)
    loader = SimpleDatasetLoader(preprocessors=[ preprocessor ])
    (images, labels) = loader(imagePaths)

    print("[INFO] Preparing Training Data")
    if trainOnly:
        trainImages = images
        # no need to set aside a test set
        testImages = np.array([])
    else:
        (trainImages, testImages, trainLabels, testLabels) = train_test_split(images, labels, test_size=0.25)

    print("[INFO] Fitting Model")
    model = MiniVGGNet.build(256,  256, 3, num_classes=np.unique(labels))
    model.fit(trainImages, trainLabels)
    print("[INFO] Model Fitting Complete")

    if trainOnly:
        print("[INFO] Testing Not Required. Proceeding To Response Preparation")
        testImages = trainImages
        testLabels = trainLabels
        # get predictions of the training set to use for the classification report
        predictions = model.predict(np.array( testImages ))
        uniqueLabels = np.unique(testLabels)

    else:
        print("[INFO] Preparing Testing Data")

        # Similar to the training set, load each image and perform a 
        # prediction on them to see what the model thinks it is
        # This prediction will be recorded for scoring later
        predictions = model.predict(testImages)
        uniqueLabels = np.unique(labels)

    print("[INFO] Scoring Model")
    accuracy = model.score(testImages, testLabels)
    classificationReport = classification_report(testLabels, predictions, labels=uniqueLabels)
    print("[INFO] Train Request Complete, Returning Training Results")

    print("[INFO] Saving Trained Model")
    modelPath = os.path.join(PKL_PATH, taskId + ".hdf5")
    model.save(modelPath)
    print("[INFO] Training Model Saved")

    print({"taskId": taskId, "modelPath": modelPath, "accuracy": accuracy, 
            **model.get_params(), "classificationReport": classificationReport})

    return {"taskId": taskId, "modelPath": modelPath, "accuracy": accuracy, 
            **model.get_params(), "classificationReport": classificationReport}
