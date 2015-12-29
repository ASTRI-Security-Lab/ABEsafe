# ABEsafe

NAS based secure file sharing system with ABE (Attribute-Based Encryption) for data encryption.
ABEsafe is developed for Unix-based system. (for Mac and Linux, tested on Mac)

ABEsafe project contains two folders, Admin and Client, which are for Admin and Clients.
Admin folder contains tools for creating ABEsafe file system environment in NAS. It is 
responsable for generate the secret keys for each user.
Client folder contains client user interface for user login, encrypting and decrypting files.

## Dependencies
ABEsafe is written in python 2.7, using `wxpython` for the GUI.
To run the scripts, `wxpython` has to be installed first.

`libabe.so` is the shared library for the underlying Ciphertext-Policy Attribute-based Encryption with 
slight performance improvement based on [John Bethencourt's implementation](http://acsc.cs.utexas.edu/cpabe/).

## Admin
To run the admin tool,
```
cd Admin
python ABEsafe_admin.py
```

Select the folder you would like to build the system on.

## Client
To run the client,
```
cd Client
python ABEsafe_main.py
```

Select the folder where an ABE system has already built.
Select the user account, and copy the passphrase which could be found in the admin tool.
