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

## Add bot to server
https://discord.com/api/oauth2/authorize?client_id=1027303885427183617&permissions=395137121344&scope=bot

