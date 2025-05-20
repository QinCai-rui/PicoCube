## 16/5/25

### Update 1/1

In around **30 minutes** I managed to create a Prove-of-Concept (PoC) version of a 3x3 Rubik's Cube scramble generator. The code is pretty simple and straightforward, so I'm not gonna waste time describing how it works.

![basic scramble generator in action](https://github.com/user-attachments/assets/4139d443-92f2-437f-946a-af215583b283)

---------------------

### Update 2/2

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

---------------------------

## 19/5/25

### Update 1/3

After about **90 minutes** of hard grind, behold -- the `PiCubeZero`. Okay, im not even sure if it works or not, since I don't have the necessary hardware to build the project physically. That also means there is no pictures to share :((.

The process was pretty straightforward, since there is sooo much documentation on the Internet about the modules I was/am after. I fed the completed program into `GPT-4.1` to check for any mistakes and suggestions, and good -- no big mistakes, but a few changes were made, such as the font selection thing I do _not_ know how it works, or if it's supposed to work... 

----------

### Update 2/4

Another **50 -ish minutes** later and I (sort of, and the stupid `GPT-4.1` helped me **a lot**) made a version of PiCube, called "PiCubePico", since it is based on the Raspberry Pi Pico MCU. Check it out here on Wokwi Simulator: <https://wokwi.com/projects/431347174552980481>

Screenshot: ![image](https://github.com/user-attachments/assets/c9dac93d-f04c-47e7-b45a-9a12dfbac601)

_(pls ignore the inconsistency between the OLED screen and the 7-seg display. The simulator is **extremely** laggy, with one second simulated being 15+ secs in real life)_

---------

### Update 3/5

Spent like **1.5 hours** creating the BOM, and it is not even complete (yet). 
Here is the BOM for RasPiCube - PiCubeZero: <https://github.com/QinCai-rui/RasPiCube/blob/PiCubeZero/BOM.md>

----------

## 20/5/25

### Update 1/6

Just updated the RasPiCube - PiCubeZero program to use a Waveshare 2-inch IPS LCD Display (ST7789, 240x320), instead of a tiny SSD1306 128x64 OLED display. This time GPT-4.1 helped me a lot when updating the program since I made quite a lot of mistakes. 

Time spent this session: ~ 

### Update 2/7

For this session, I worked a lot on the [PiCubeZero's BOM](https://github.com/QinCai-rui/RasPiCube/blob/PiCubeZero/BOM.md). I tried comparing the items I need on Aliexpress and Amazon. I almost got scammed by (likely) a scam on Aliexpress. [Link](https://www.aliexpress.com/item/1005008269997334.html)

The "Sandian" branded uSD cards look sooo similar to the real "SanDisk" ones.

<img width="311" alt="Screenshot 2025-05-20 at 6 42 54 PM" src="https://github.com/user-attachments/assets/4dbae5fb-b5d5-4295-ab59-7e451d6c4774" />
<img width="539" alt="Screenshot 2025-05-20 at 6 43 13 PM" src="https://github.com/user-attachments/assets/e4387966-cdeb-495c-a4e3-ea30907f4333" />

A quick Internet search revealed that...... "SanDian" is a scam. WHOO HOO. /j

Here are the posts:
[post1](https://forums.grc.com/threads/fake-1tb-sandian-micro-sdcard-test.1333/) 
[post2](https://bulkmemorycards.com/identifying-counterfeit-microsd-cards/)

Maybe just don't buy uSD cards from AliExpress... Buy them on Amazon instead ig.
