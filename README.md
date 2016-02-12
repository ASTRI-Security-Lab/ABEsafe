# ABEsafe

### Securing your data on shared platform with Attribute-Based Encryption

This is a NAS based encrypted secure file sharing system for a workspace with users 
having multiple roles and identities, in a simple fashion for management. 
ABEsafe is developed for Unix-based system. (for Mac and Linux, tested on Mac)

paper: [Ciphertext-Policy Attribute-Based Encryption](https://www.cs.utexas.edu/~bwaters/publications/papers/cp-abe.pdf)

ABEsafe project contains two folders, Admin and Client, which are for Admin and Clients.
Admin folder contains tools for creating ABEsafe file system environment in NAS. It is 
responsable for generate the secret keys for each user.
Client folder contains client user interface for user login, encrypting and decrypting files.

## Dependencies
ABEsafe is written in python 2.7, using `wxpython` for the GUI.
To run the scripts, `wxpython` has to be installed first.

`libabe.so` is the shared library for the underlying Ciphertext-Policy Attribute-based Encryption with 
slight performance improvement based on [John Bethencourt's implementation](http://acsc.cs.utexas.edu/cpabe/).

## Installation
You can simply run the script `setup.sh` to install all dependencies:
```
sh ABEsafe/setup.sh
```
It could take a long time to build and install wxpython.

### Alternatives
If the script does not work for you, you may try installing it step by step.
First, install python, on Mac using homebrew:
```
brew install python
```
Install wxpython,
```
pip install --upgrade pip
pip install --upgrade --trusted-host wxpython.org --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
```
Download this repository, with git:
```
git clone https://github.com/ASTRI-Security-Lab/ABEsafe
cd ABEsafe
```

## Using ABEsafe
Before building the system, create or finding a sharing folder in a mounted NAS, (e.g.`/Volumes/SharedFolder`)

Use the admin tool to generate the keys and attributes for each user. A sample user set is provided for testing.

## Admin
To run the admin tool,
```
cd Admin
python ABEsafe_admin.py
```
Short demo: [Admin tool demo](https://www.youtube.com/watch?v=b140-TauYIU)

Select the folder you would like to build the system on.
You can then create a new user, or retrieve the passphrase of an existing user.

## Client
To run the client,
```
cd Client
python ABEsafe_main.py
```
Short demo: [Client application demo](https://www.youtube.com/watch?v=MbeI-toh4nI)

Select the folder where an ABE system has already built.
Select the user account, and copy the passphrase which could be found in the admin tool.

### Client Application Screenshot
<img src="https://github.com/ASTRI-Security-Lab/ABEsafe/blob/master/sample/client.png" width="704" height="576">

After logging in, you are now able to browse the folder tree. By default, there should be no file inside if the folder is newly created. Otherwise, original files will still be there, and is only visible if the bottom-left `All shown` checkbox is checked.
You may drag folder or select the folder you want to share, and select the corresponding policy which fits the sharees.

### Policy Selection Screenshot
<img src="https://github.com/ASTRI-Security-Lab/ABEsafe/blob/master/sample/policy.png" width="640" height="480">
