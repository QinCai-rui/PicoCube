## 16/5/25

### Update 1

In around **30 minutes** I managed to create a Prove-of-Concept (PoC) version of a 3x3 Rubik's Cube scramble generator. The code is pretty simple and straightforward, so I'm not gonna waste time describing how it works.

![basic scramble generator in action](https://github.com/user-attachments/assets/4139d443-92f2-437f-946a-af215583b283)

---------------------

### Update 2

Another **1 hour and a bit**, a _proper_ timer and scramble generator was born. I integrated the old scrable generator into the new program, by importing it as a module.

I kind of struggled at first to make the timing work, because the code on line 31 somehow "redefined" the `time` module, which gave me wheird errors:

```python
Traceback (most recent call last):
  File "/home/qincai/PicoCube/test.py", line 76, in <module>
    main()
    ~~~~^^
  File "/home/qincai/PicoCube/test.py", line 51, in main
    start_time = time.time()
                 ^^^^
UnboundLocalError: cannot access local variable 'time' where it is not associated with a value
```
so i changed `time` to `solve_time` :))

Another challenge was to display the real-time timer, which every rubiks cube timer should have. In the older real-time version of this program, the user had to press `CTRL+C` to trigger the timer stop, which is not ideal. Fortunately I worked _that_ out as well, using `threading`
