# Donkeycar: a python self driving library working with mpad. 
Install on main pi. 
```
wget https://raw.githubusercontent.com/ishan190425/DonkeyCustom/main/mpad.sh && chmod +x mpad.sh && ./mpad.sh
```
Install on object detection pi.
```
wget https://raw.githubusercontent.com/ishan190425/DonkeyCustom/main/objectdetection.sh && chmod +x objectdetection.sh && ./objectdetection.sh
```


Model: "linear"
__________________________________________________________________________________________________
 Layer (type)                   Output Shape         Param #     Connected to                     
==================================================================================================
 img_in (InputLayer)            [(None, 120, 160, 3  0           []                               
                                )]                                                                
                                                                                                  
 conv2d (Conv2D)                (None, 58, 78, 24)   1824        ['img_in[0][0]']                 
                                                                                                  
 conv2d_1 (Conv2D)              (None, 27, 37, 32)   19232       ['conv2d[0][0]']                 
                                                                                                  
 conv2d_2 (Conv2D)              (None, 12, 17, 64)   51264       ['conv2d_1[0][0]']               
                                                                                                  
 conv2d_3 (Conv2D)              (None, 10, 15, 64)   36928       ['conv2d_2[0][0]']               
                                                                                                  
 conv2d_4 (Conv2D)              (None, 8, 13, 64)    36928       ['conv2d_3[0][0]']               
                                                                                                  
 flatten (Flatten)              (None, 6656)         0           ['conv2d_4[0][0]']               
                                                                                                  
 dense (Dense)                  (None, 100)          665700      ['flatten[0][0]']                
                                                                                                  
 dropout (Dropout)              (None, 100)          0           ['dense[0][0]']                  
                                                                                                  
 dense_1 (Dense)                (None, 50)           5050        ['dropout[0][0]']                
                                                                                                  
 dropout_1 (Dropout)            (None, 50)           0           ['dense_1[0][0]']                
                                                                                                  
 n_outputs0 (Dense)             (None, 1)            51          ['dropout_1[0][0]']              
                                                                                                  
 n_outputs1 (Dense)             (None, 1)            51          ['dropout_1[0][0]']              
                                                                                                  
==================================================================================================
Total params: 817,028
Trainable params: 817,028
Non-trainable params: 0
__________________________________________________________________________________________________
