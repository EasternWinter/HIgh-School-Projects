#Nathan Yu; ICS3U; Dec 20, 2024; Inna Ellacott
#This is a game where you play as a desert sparrow.
#You are flying through a cactus grove.
#Avoid the cacti.

import random as rand
import pygame as pyg
import tkinter as tk
import turtle as turt
import time as tim

#Global variables
maxScore = 0
score = 0
seedCount = 0
pipeSpeed = -5

#Create initial screen and name.
root = tk.Tk()
root.title("Desert Sparrow")

topFrame = tk.Frame(root)
topFrame.grid(row = 0, column = 0)
bottomFrame = tk.Frame(root, width=600, height=80)
bottomFrame.grid(row = 1, column = 0)

#Sound
pyg.mixer.init()
channel1 = pyg.mixer.Channel(0)
channel2 = pyg.mixer.Channel(1)
channel3 = pyg.mixer.Channel(2)
background = pyg.mixer.Sound("background.mp3")
jump = pyg.mixer.Sound("jump.mp3")
endSound = pyg.mixer.Sound("end.mp3")

#Start game
def startGame():
    global pipeSpeed, score
    pipeSpeed = -5

    score = 0
    game()

#Update score
def updateScore(display):
    global score
    display.clear()
    display.write(f"Score: {score}", move=False, align="center", font=("Arial", 20))

def updateSeed(seedDisplay):
    global seedCount
    seedDisplay.clear()
    seedDisplay.write(f"Seed: {seedCount}", move=False, align="center", font=("Arial", 20))

#Go up
def goUp(player):
    channel2.play(jump)
    player.dy += 8
    if player.dy > 8:
        player.dy = 8

#End game
def gameOver(canvas):
    global maxScore, score, seedCount
    total = score + seedCount * 3
    maxScore = max(total, maxScore)
    canvas.destroy()

    channel1.pause()
    channel3.play(endSound)

    #Ask if want to play again and display high score.
    result = tk.messagebox.askyesno("Try Again?", f"High Score: {maxScore} \n Your Score: {total}")
    if result:
        startGame()
    else:
        exit()

def game():
    channel1.play(background, -1)
    
    canvas = tk.Canvas(topFrame, width = 600, height = 720)
    canvas.pack()

    #Player or desert sparrow.
    player = turt.RawTurtle(canvas)
    player.screen.bgpic('desert.gif')
    player.screen.addshape('desertSparrow.gif')
    player.shape("desertSparrow.gif")
    player.penup()
    player.dx = -200
    player.dy = 0
    player.goto(-200, 0)

    #Records score and game state.
    display = turt.RawTurtle(canvas)
    display.hideturtle()
    display.penup()
    display.pencolor('blue')
    display.goto(0, 15)
    display.write("Score: 0", move=False, align="center", font=("Arial", 20))

    #Power up / Seed
    seed = turt.RawTurtle(canvas)
    seed.screen.addshape('seed.gif')
    seed.shape("seed.gif")
    seed.speed(0)
    seed.penup()
    seed.goto(rand.randint(620, 880), rand.randint(-20, 20))

    #Seed count
    seedDisplay = turt.RawTurtle(canvas)
    seedDisplay.hideturtle()
    seedDisplay.penup()
    seedDisplay.goto(0, -15)
    seedDisplay.write("Seeds: 0", move=False, align="center", font=("Arial", 20))

    #Cacti
    cacti = []
    xcord = [300, 600, 900]
    yTopCord = [300, 380, 360]
    yBotCord = [-300, -220, -240]
    for i in range(3):
        pair = []

        cactusTop = turt.RawTurtle(canvas)
        cactusTop.screen.addshape("cactusTop.gif")
        cactusTop.shape("cactusTop.gif")
        cactusTop.speed(0)
        cactusTop.penup()
        cactusTop.goto(xcord[i], yTopCord[i])
        cactusTop.dy = 0
        pair.append(cactusTop)

        cactusBot = turt.RawTurtle(canvas)
        cactusBot.screen.addshape("cactus.gif")
        cactusBot.shape("cactus.gif")
        cactusBot.speed(0)
        cactusBot.penup()
        cactusBot.goto(xcord[i], yBotCord[i])
        cactusBot.dy=0
        pair.append(cactusBot)
        cacti.append(pair)
    
    #On space, go up
    root.bind('<space>', lambda event: goUp(player))

    #Initialize game variables
    gravity = -0.3
      
    #Game loop
    def gameLoop():
        global pipeSpeed, score, seedCount
        #Pause
        tim.sleep(0.02)
        #Update the screen
        canvas.update()

        #Add gravity
        player.dy += gravity

        #Move player
        y = player.ycor()
        y += player.dy
        player.sety(y)
       
        #Bottom border
        if player.ycor() < -340:
            player.dy = 0
            player.sety(-340)

        #Iterate through pipes
        for pair in cacti:
            top = pair[0]
            bot = pair[1]
           
            #Move pipe
            x = top.xcor()
            x += pipeSpeed
            top.setx(x)
           
            x = bot.xcor()
            x += pipeSpeed
            bot.setx(x)

            x = seed.xcor()
            x+= pipeSpeed/3
            seed.setx(x)
           
            #Return pipes to start
            if top.xcor() < -250:
                top.setx(600)
                bot.setx(600)
                top.value = 1

            #Check is on either side of pipe.
            if (player.dx + 30 > top.xcor() - 30) and (player.dx - 30 < top.xcor() + 30):
                #Check if touching top
                if (player.ycor() + 20 > top.ycor() - 220) or (player.ycor() - 20 < bot.ycor() + 220):
                    gameOver(canvas)

            if (abs(player.dx - seed.xcor()) < 30) and (abs(player.ycor() - seed.ycor()) < 30):
                pipeSpeed += 3
                seed.goto(rand.randint(620, 680), rand.randint(-20, 20))
                seedCount += 1
                updateSeed(seedDisplay)
            elif player.dx - seed.xcor() > 30:
                seed.goto(rand.randint(620, 680), rand.randint(-20, 20))

            #Update score once passed pipes      
            if (top.xcor() + 30 < player.dx - 15):
                score += 1
                display.clear()
                updateScore(display)
                if score % 3 == 0:
                    pipeSpeed -= 3

        root.after(20, gameLoop)
    root.after(20, gameLoop)

def help():
    wn = tk.Toplevel(root)
    wn.title("Help")
    rules = """
    Desert Sparrow:
    1. Click the button "Start Game"
    2. Press space to jump.
    3. Avoid the cacti as much as possible.
    4. To slow down the speed, get the golden seed that appears at random locations.
    ---------------------------------------
    Note:
    Speed will increase for every three points scored.
    The seed is worth 3 points at the end.
    """
    
    label = tk.Label(wn, text = rules, font=("Times New Roman", 15), bg='#ff9933', justify="left")
    label.pack(padx=20, pady=20)
    close_button = tk.Button(wn, text="Close", command=wn.destroy)
    close_button.pack(pady=10, side=tk.BOTTOM)

#Controls
start = tk.Button(bottomFrame, text="Start Game", bg='Purple', command=startGame)
start.grid(row=1, column=0, padx=10)

about = tk.Button(bottomFrame, text="Help", command=help)
about.grid(row=1, column=2, padx=10)

end = tk.Button(bottomFrame, text="Quit Game", bg='Red', command=exit)
end.grid(row=1, column=10, padx=10)

root.mainloop()