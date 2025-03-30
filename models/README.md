# Vosk Models Directory

This directory is where you should place the Vosk speech recognition models used for transcription.

## Downloading Models

1. Visit the Vosk models page: [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)

2. Download a model appropriate for your language and needs:
   - For English, recommended models:
     - Small model (good for testing): `vosk-model-small-en-us-0.15` (~40MB)
     - Standard model (better accuracy): `vosk-model-en-us-0.22` (~1.8GB)
   - Models are available for many other languages as well

3. Extract the downloaded ZIP file into this directory.
   For example, if you downloaded `vosk-model-small-en-us-0.15.zip`, after extraction you should have:
   ```
   models/
   └── vosk-model-small-en-us-0.15/
       ├── am/
       ├── conf/
       ├── graph/
       ├── ivector/
       ├── rescore/
       └── README
   ```

4. Update the `model_path` in your `config.ini` file to point to the model directory:
   ```ini
   [transcription]
   model_path = models/vosk-model-small-en-us-0.15
   ```

## Model Selection

- **Small models** (< 50MB): Good for testing and quick transcription, but less accurate
- **Medium models** (100-500MB): Good balance between accuracy and resource usage
- **Large models** (> 1GB): Best accuracy, but require more memory and processing power

Choose a model based on your needs and available resources.

## Troubleshooting

If you encounter issues with transcription:

1. Make sure the model path in `config.ini` is correct
2. Verify that the model directory contains all the necessary files
3. Try a different model if you're having accuracy issues
4. Check the logs for any error messages related to the model loading

For more information, see the main [TRANSCRIPTION.md](../TRANSCRIPTION.md) documentation.
