import os
import pathlib
from pathlib import Path
from app import models
from flask import render_template, request
import subprocess as sp
from app import app, db
from app.source.utils import utils
from app.models import Dataset
from app.source.preprocessingDataset.PreprocessingControl import preprocessing
from app.source.utils import getlog as log
from app.source.validazioneDataset.ValidazioneControl import valida
from app.source.classificazioneDataset.ClassificazioneControl import classify
from app.source.classificazioneDataset.ClassificazioneControl import getClassifiedDataset

@app.route('/')
@app.route('/home')
def homepage():  # put application's code here
    return render_template('index.html')


@app.route('/formcontrol', methods=['GET', 'POST'])
def smista():
    print('Request send on ')
    ROOT_DIR = pathlib.Path(__file__).cwd()
    # log.log()
    file = request.files.get('userfile')
    ext_ok = ['txt', 'csv', 'data']
    temp = file.filename
    extension = temp.split('.')[-1]
    print(extension)
    if not ext_ok.__contains__(extension):
        return 'Il file ha un estensione non ammessa!'

    if file is None:
        return 'No Train set uploaded'

    uploaddir = ROOT_DIR / 'upload_dataset/'
    userfile_name = file.filename
    userpath = uploaddir / userfile_name

    if file.content_length > 80000000:
        return 'Il file è troppo grande!'
    prototypeSelection = request.form.get('reduce1')
    featureExtraction = request.form.get('reduce')
    autosplit = request.form.get('test')

    file.save(userpath)
    print("Dataset: ", file.filename)
    # Recupero le impostazioni dell'utente, cioè
    # quali operazioni vuole effettuare e, in caso di QSVM, anche il token
    print("AutoSplit: ", autosplit)
    numRawsPS = 200  # numero di righe dopo la Prototype Selection con GA
    print("Prototype Selection: ", prototypeSelection)
    numColsFE = 2  # numero di colonne dopo la Feature Extraction con PCA
    print("Feature Extraction: ", featureExtraction)
    #kFold= request.form.get('kFold') da inserire nel form
    kFold = False
    # doQSVM= request.form.get('QSVM') da inserire nel form
    doQSVM = True
    #token= request.form.get('token') da inserire nel form
    token='43a75c20e78cef978267a3bdcdb0207dab62575c3c9da494a1cd344022abc8a326ca1a9b7ee3f533bb7ead73a5f9fe519691a7ad17643eecbe13d1c8c4adccd2'

    # Validazione
    if autosplit or kFold:
        valida(userpath, autosplit, kFold)

    # Preprocessing
    if prototypeSelection or featureExtraction:
        preprocessing(userpath, prototypeSelection, featureExtraction, numRawsPS, numColsFE)

    # Classificazione
    #backend=request.form.get("backend")

    numCols = utils.numberOfColumns(userpath)
    features = utils.createFeatureList(numCols - 1)
    features1 = features.copy()
    features1.append("labels")
    featuresPCA = utils.createFeatureList(numColsFE)
    if doQSVM and featureExtraction:
        # facciamo QSVM con i dati della FE ovvero
        result = classify('Data_PCA_training.csv', 'Data_PCA_testing.csv', featuresPCA, token, 2)
        getClassifiedDataset(result)
    elif doQSVM and not featureExtraction:
        # facciamo QSVM senza FE
        result: dict = classify('IdFeatureDataset_compatted.csv', 'IdData_Testing_compatted.csv', features, token, len(features), "ibmq_jakarta")#backend
        getClassifiedDataset(result)
    return "ora classifica"

