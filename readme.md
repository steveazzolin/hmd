# Human-Machine Dialogue final project

This is the final project for the course Human-Machine Dialogue of the AIS MSc degree at the university of Trento.
For more information about the project, please check out `report.pdf`.


## Prerequisites
```
conda env create -f environment.yml
```

## Running the code

For interacting with the agent:
```
rasa run actions
rasa shell
```

For starting an interactive learning session:
```
rasa run actions
rasa interactive
```


## Deploying to Amazon Alexa

```
rasa run actions
rasa run -m models --endpoints endpoints.yml -p 5005
ngrok http 5005
```