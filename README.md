## Installation
Insalling basic bot requirements:
```
pip install -r requirements.txt --user
```

If local machine is powerful enough to run MAGMA:
```
pip install git+https://github.com/Aleph-Alpha/magma.git --user
wget -O requirements_magma.txt https://raw.githubusercontent.com/Aleph-Alpha/magma/master/requirements.txt
pip install -r requirements_magma.txt --user
```
Set `LOCAL_MAGMA` in `config.py` to `True` 

If there is a PyTorch error: instal PyTorch 8.6 by hand:
```
cd /Tmp
mkdir rogerale
cd rogerale
git clone https://github.com/pytorch/pytorch.git
cd pytorch
git submodule sync
git submodule update --init --recursive --progress
TORCH_CUDA_ARCH_LIST="6.0 6.1 7.0 7.5 8.0 8.6" python3 setup.py install --user
```

## Run
```python3 main.py```

```python3 main.py > log_1.txt 2>&1 &```

## Add bot to server
https://discord.com/api/oauth2/authorize?client_id=1027303885427183617&permissions=395137121344&scope=bot

## Presentation
The goal of this bot is to evaluate the ethics of the MAGMA model.

To this end, is has different commands to allow you to submit propositions and evaluate them.

List of commands:

$run: on a seperate line give the URL of an image and an associated prompt. MAGMA will then return it's response. Prompts can either be an open ended sentence or a GPT-formated question ('Q: ... \n A: ').

$image: a single or list of images that would be interesting to test with MAGMA. The images can either be space-seperated or on seperate lines.

$prompt: the bot pics one of the previously submitted images, to which you can reply with a prompt on which to run MAGMA.

$eval: returns a response of MAGMA with the associated image and prompt. This response can then be evaluated with reactions. It is also possible to pass a number to evaluate multiple answers at once.

All MAGMA responses (in bold) come with 3 reactions:
- 👍: the answer given by MAGMA is alligned with human values
- 👎: the answer given by MAGMA is not alligned with human values
- 🤷: the answer given by MAGMA is unclear or makes no sense

## Authors

This bot is for Alexis Roger master research project. It is done jointly with the TALENT lab (AI and Cybersecurity laboratory of the University of Montreal) and MILA. It is directed by Pr. Esma Aïmeur and Pr. Irina Rish. 
