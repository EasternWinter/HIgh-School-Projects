#Nathan Yu; ICS3U; Dec 20, 2024; Inna Ellacott
#This is a game where you play as a desert sparrow.
#You are flying through a cactus grove.
#Avoid the cacti.

import pygame as pyg
import tkinter as tk
import turtle as turt
import time as tim

#Global variables
maxScore = 0
score = 0
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
    display.write(f"Score: {score}", move=False, align="center", font=("Arial", 20, "normal"))

#Go up
def goUp(player):
    channel2.play(jump)
    player.dy += 8
    if player.dy > 8:
        player.dy = 8

#End game
def gameOver(canvas):
    global maxScore, score
    maxScore = max(score, maxScore)
    canvas.destroy()

    channel1.pause()
    channel3.play(endSound)

    #Ask if want to play again and display high score.
    result = tk.messagebox.askyesno("Try Again?", f"High Score: {maxScore} \n Your Score: {score}")
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
    display.write("Score: 0", move=False, align="center", font=("Arial", 20, "normal"))

    #Pipes
    cactus1Top = turt.RawTurtle(canvas)
    cactus1Top.screen.addshape("cactusTop.gif")
    cactus1Top.shape("cactusTop.gif")
    cactus1Top.speed(0)
    cactus1Top.penup()
    cactus1Top.goto(300, 300)
    cactus1Top.dy = 0

    cactus1Bot = turt.RawTurtle(canvas)
    cactus1Bot.screen.addshape("cactus.gif")
    cactus1Bot.shape("cactus.gif")
    cactus1Bot.speed(0)
    cactus1Bot.penup()
    cactus1Bot.goto(300, -300)
    cactus1Bot.dy = 0

    cactus2Top = turt.RawTurtle(canvas)
    cactus2Top.screen.addshape("cactusTop.gif")
    cactus2Top.shape("cactusTop.gif")
    cactus2Top.speed(0)
    cactus2Top.penup()
    cactus2Top.goto(600, 380)
    cactus2Top.dy = 0

    cactus2Bot = turt.RawTurtle(canvas)
    cactus2Bot.screen.addshape("cactus.gif")
    cactus2Bot.shape("cactus.gif")
    cactus2Bot.speed(0)
    cactus2Bot.penup()
    cactus2Bot.goto(600, -220)

    cactus3Top = turt.RawTurtle(canvas)
    cactus3Top.screen.addshape("cactusTop.gif")
    cactus3Top.shape("cactusTop.gif")
    cactus3Top.speed(0)
    cactus3Top.penup()
    cactus3Top.goto(900, 260)
    cactus3Top.dy = 0

    cactus3Bot = turt.RawTurtle(canvas)
    cactus3Bot.screen.addshape("cactus.gif")
    cactus3Bot.shape("cactus.gif")
    cactus3Bot.speed(0)
    cactus3Bot.penup()
    cactus3Bot.goto(900, -440)

    #All cacti pairs
    cacti = [(cactus1Top, cactus1Bot), (cactus2Top, cactus2Bot), (cactus3Top, cactus3Bot)]

    #On space, go up
    root.bind('<space>', lambda event: goUp(player))

    #Initialize game variables
    player.score = 0
    gravity = -0.3 
      
    #Game loop
    def gameLoop():
        global pipeSpeed, score
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

            #Update score once passed pipes      
            if (top.xcor() + 30 < player.dx - 15):
                score += 1
                display.clear()
                updateScore(display)
                if score % 3 == 0:
                    pipeSpeed -= 2

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
    ---------------------------------------
    Note:
    Speed will increase for every three points scored.
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