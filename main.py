import base64
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import random
import re
import secrets
import smtplib
import ssl
import string
import tempfile
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import aiomysql
from bs4 import BeautifulSoup
from fastapi import (Depends, FastAPI, File, Form, status, HTTPException, Query, UploadFile, requests,)
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
import httpx
from jose import jwt, JWTError
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
from moviepy.editor import VideoFileClip
import requests


# Load environment variables from .env file
load_dotenv()

app = FastAPI()

 

sync_db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


async_db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_NAME"),
    "port": 3306,
    "minsize": 4,
    "maxsize": 16,
    "autocommit": True,
    # 'ssl': {},
}

conn = mysql.connector.connect(**sync_db_config)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ravoom.com" , "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
pool = None

 
@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
 
    pool = await aiomysql.create_pool(**async_db_config)
    print("Database pool created.")
    await create_tables()
    try:
        
        yield
    finally:
  
        pool.terminate()
        await pool.wait_closed()
        print("Database pool terminated.")

 
app.router.lifespan_context = lifespan




async def create_tables():
    try:
        async with aiomysql.create_pool(**async_db_config) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:

                    
                    create_comment_table_query = """
                    CREATE TABLE IF NOT EXISTS comment (
                        commentid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        text VARCHAR(5000) DEFAULT NULL,
                        commenteddate DATETIME DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        scrollposition INT(11) DEFAULT NULL,
                        n_or_g TINYTEXT DEFAULT NULL, 
                        commentimage LONGBLOB DEFAULT NULL,
                        PRIMARY KEY (commentid),
                        KEY postid (postid),
                        KEY userid (userid),
                        CONSTRAINT comment_ibfk_1 FOREIGN KEY (postid) REFERENCES post (postid),
                        CONSTRAINT comment_ibfk_2 FOREIGN KEY (userid) REFERENCES user (userid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_comment_table_query)
                    print("Table 'comment' created successfully.")
                    
                    
                    
                    
                    create_commentreply_table_query = """
                    CREATE TABLE IF NOT EXISTS commentreply (
                        commentreplayid INT(11) NOT NULL AUTO_INCREMENT,
                        commentid INT(11) DEFAULT NULL,
                        postid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        text VARCHAR(1000) DEFAULT NULL,
                        replayeddate DATETIME DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        n_or_g TINYTEXT DEFAULT NULL,
                        PRIMARY KEY (commentreplayid),
                        KEY commentid (commentid),
                        CONSTRAINT commentreply_ibfk_1 FOREIGN KEY (commentid) REFERENCES comment (commentid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_commentreply_table_query)
                    print("Table 'commentreply' created successfully.")
                    
                    
                    
                    
                    
                    create_forgetpassword_table_query = """
                    CREATE TABLE IF NOT EXISTS forgetpassword (
                        forgetpasswordtid INT(11) NOT NULL AUTO_INCREMENT,
                        userid INT(11) NOT NULL,
                        code VARCHAR(100) NOT NULL,
                        emailaddress VARCHAR(1000) DEFAULT NULL,
                        expiredornot VARCHAR(100) NOT NULL,
                        sentdate DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (forgetpasswordtid),
                        KEY userid (userid),
                        CONSTRAINT forgetpassword_ibfk_1 FOREIGN KEY (userid) REFERENCES user (userid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_forgetpassword_table_query)
                    print("Table 'forgetpassword' created successfully.")
                    
                    
                    
                    
                    
                    create_groupcomment_table_query = """
                    CREATE TABLE IF NOT EXISTS groupcomment (
                        commentid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        text VARCHAR(5000) DEFAULT NULL,
                        commenteddate DATETIME DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        n_or_g TINYTEXT DEFAULT NULL, 
                        commentimage LONGBLOB DEFAULT NULL,
                        PRIMARY KEY (commentid),
                        KEY userid (userid),
                        KEY postid (postid),
                        CONSTRAINT groupcomment_ibfk_1 FOREIGN KEY (userid) REFERENCES user (userid),
                        CONSTRAINT groupcomment_ibfk_2 FOREIGN KEY (postid) REFERENCES grouppost (postid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_groupcomment_table_query)
                    print("Table 'groupcomment' created successfully.")
                    
                    
                    
                    
                    
                    
                    
                    create_groupcommentreplay_table_query = """
                    CREATE TABLE IF NOT EXISTS groupcommentreplay (
                        commentreplayid INT(11) NOT NULL AUTO_INCREMENT,
                        commentid INT(11) DEFAULT NULL,
                        postid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        text VARCHAR(1000) DEFAULT NULL,
                        replayeddate DATETIME DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        n_or_g TINYTEXT DEFAULT NULL, 
                        PRIMARY KEY (commentreplayid),
                        KEY userid (userid),
                        KEY postid (postid),
                        CONSTRAINT groupcommentreplay_ibfk_1 FOREIGN KEY (userid) REFERENCES user (userid),
                        CONSTRAINT groupcommentreplay_ibfk_2 FOREIGN KEY (postid) REFERENCES grouppost (postid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_groupcommentreplay_table_query)
                    print("Table 'groupcommentreplay' created successfully.")
                    
                    
                    
                    
                    create_groupimage_table_query = """
                    CREATE TABLE IF NOT EXISTS groupimage (
                        imageid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        image LONGBLOB DEFAULT NULL,
                        PRIMARY KEY (imageid),
                        KEY postid (postid),
                        CONSTRAINT groupimage_ibfk_1 FOREIGN KEY (postid) REFERENCES grouppost (postid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_groupimage_table_query)
                    print("Table 'groupimage' created successfully.")
                    
                    
                    
                    
                    create_groupmembercount_table_query = """
                    CREATE TABLE IF NOT EXISTS groupmembercount (
                        groupmembercountid INT(11) NOT NULL AUTO_INCREMENT,
                        groupid INT(11) DEFAULT NULL,
                        groupownerid INT(11) DEFAULT NULL,
                        grouptype VARCHAR(100) NOT NULL,
                        groupname VARCHAR(100) DEFAULT NULL,
                        groupimage LONGBLOB DEFAULT NULL,
                        members INT(11) DEFAULT NULL,
                        PRIMARY KEY (groupmembercountid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """
                    await cursor.execute(create_groupmembercount_table_query)
                    print("Table 'groupmembercount' created successfully.")
                    
                    
                    
                    
                    
                    create_grouppost_table_query = """
                    CREATE TABLE IF NOT EXISTS grouppost (
                        postid INT(11) NOT NULL AUTO_INCREMENT,
                        groupid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        postdescription VARCHAR(1000) DEFAULT NULL,
                        posteddate DATETIME DEFAULT NULL,
                        posttype VARCHAR(50) DEFAULT NULL,
                        post LONGBLOB DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        filepath VARCHAR(1000) DEFAULT NULL,
                        groupname VARCHAR(1000) DEFAULT NULL,
                        textcolor VARCHAR(50) DEFAULT NULL,
                        textbody VARCHAR(1000) DEFAULT NULL,
                        popularcount INT(255) DEFAULT NULL,
                        thelink VARCHAR(1000) DEFAULT NULL,
                        n_or_g VARCHAR(5) NOT NULL DEFAULT 'g',
                        PRIMARY KEY (postid),
                        KEY (userid),
                        KEY (groupid),
                        CONSTRAINT `grouppost_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `user` (`userid`),
                        CONSTRAINT `grouppost_ibfk_2` FOREIGN KEY (`groupid`) REFERENCES `groups` (`groupid`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

           
                    await cursor.execute(create_grouppost_table_query)
                    print("Table 'grouppost' created successfully.")
                    
                    
                    
                    
                    
                    create_groups_table_query = """
                    CREATE TABLE IF NOT EXISTS groups (
                        groupid INT(11) NOT NULL AUTO_INCREMENT,
                        groupownerid INT(11) NOT NULL,
                        groupname VARCHAR(100) NOT NULL,
                        grouptype VARCHAR(100) DEFAULT NULL,
                        groupimage LONGBLOB DEFAULT NULL,
                        groupimageupdateddate DATETIME DEFAULT NULL,
                        groupbackgroundimage LONGBLOB DEFAULT NULL,
                        groupbackgroundimageupdateddate DATETIME DEFAULT NULL,
                        createdate DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (groupid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

 
                    await cursor.execute(create_groups_table_query)
                    print("Table 'groups' created successfully.")
                    
                    
                    
                    
                    
                    create_group_post_like_table_query = """
                    CREATE TABLE IF NOT EXISTS group_post_like (
                        likeid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        currentuserid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        profileimage LONGBLOB DEFAULT NULL,
                        PRIMARY KEY (likeid),
                        KEY postid (postid),
                        KEY userid (userid),
                        CONSTRAINT group_post_like_ibfk_1 FOREIGN KEY (postid) REFERENCES grouppost (postid),
                        CONSTRAINT group_post_like_ibfk_2 FOREIGN KEY (userid) REFERENCES user (userid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

             
                    await cursor.execute(create_group_post_like_table_query)
                    print("Table 'group_post_like' created successfully.")
                    
                    
                    
                    
                    create_group_users_table_query = """
                    CREATE TABLE IF NOT EXISTS group_users (
                        groupuser_id INT(11) NOT NULL AUTO_INCREMENT,
                        groupid INT(11) NOT NULL,
                        userid INT(11) NOT NULL,
                        profileimage LONGBLOB DEFAULT NULL,
                        username VARCHAR(100) NOT NULL,
                        usertype VARCHAR(100) NOT NULL,
                        joined_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TINYINT(4) NOT NULL DEFAULT 1,
                        PRIMARY KEY (groupuser_id),
                        KEY groupid (groupid),
                        KEY userid (userid),
                        CONSTRAINT group_users_ibfk_1 FOREIGN KEY (groupid) REFERENCES groups (groupid) ON DELETE CASCADE,
                        CONSTRAINT group_users_ibfk_2 FOREIGN KEY (userid) REFERENCES user (userid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

            
                    await cursor.execute(create_group_users_table_query)
                    print("Table 'group_users' created successfully.")
                    
                    
                    
                    
                    
                    
                    
                    
                    create_iamfollowed_table_query = """
                    CREATE TABLE IF NOT EXISTS iamfollowed (
                        iamfollowedid INT(11) NOT NULL AUTO_INCREMENT,
                        myuserid INT(11) DEFAULT NULL,
                        otheruserid INT(11) DEFAULT NULL,
                        username VARCHAR(100) NOT NULL,
                        profile LONGBLOB DEFAULT NULL,
                        date DATETIME DEFAULT NULL,
                        PRIMARY KEY (iamfollowedid),
                        KEY myuserid (myuserid),
                        CONSTRAINT iamfollowed_ibfk_1 FOREIGN KEY (myuserid) REFERENCES user (userid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

          
                    await cursor.execute(create_iamfollowed_table_query)
                    print("Table 'iamfollowed' created successfully.")
                    
                    
                    
                    
                    
                    create_iamfollowing_table_query = """
                    CREATE TABLE IF NOT EXISTS iamfollowing (
                        iamfollowingid INT(11) NOT NULL AUTO_INCREMENT,
                        myuserid INT(11) DEFAULT NULL,
                        otheruserid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        profile LONGBLOB DEFAULT NULL,
                        date DATETIME DEFAULT NULL,
                        type VARCHAR(50) DEFAULT NULL,
                        groupid INT(11) DEFAULT NULL,
                        PRIMARY KEY (iamfollowingid),
                        KEY myuserid (myuserid),
                        CONSTRAINT iamfollowing_ibfk_1 FOREIGN KEY (myuserid) REFERENCES user (userid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_iamfollowing_table_query)
                    print("Table 'iamfollowing' created successfully.")
                    
                    
                    
                    
                    create_image_table_query = """
                    CREATE TABLE IF NOT EXISTS image (
                        imageid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        image LONGBLOB DEFAULT NULL,
                        PRIMARY KEY (imageid),
                        KEY postid (postid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_image_table_query)
                    print("Table 'image' created successfully.")
                    
                    
                    
                    
                    
                    
                    
                    create_notification_table_query = """
                    CREATE TABLE IF NOT EXISTS notification (
                        notificationid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        postowneruserid INT(11) DEFAULT NULL,
                        myuserid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        notificationtype VARCHAR(50) DEFAULT NULL,
                        commenttext VARCHAR(1000) DEFAULT NULL,
                        replaytext VARCHAR(1000) DEFAULT NULL,
                        date DATETIME DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        seenstatus TINYINT(4) DEFAULT NULL,
                        groupid INT(11) DEFAULT NULL,
                        groupname VARCHAR(100) DEFAULT NULL,
                        n_or_g VARCHAR(5) NOT NULL DEFAULT 'n',
                        PRIMARY KEY (notificationid),
                        KEY postid (postid),
                        KEY postowneruserid (postowneruserid),
                        KEY myuserid (myuserid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_notification_table_query)
                    print("Table 'notification' created successfully.")
                    
                    
                    create_user_blocked_table_query = """
                        CREATE TABLE IF NOT EXISTS user_blocked (
                            blockedid INT(11) NOT NULL AUTO_INCREMENT,
                            userid INT(11) DEFAULT NULL,
                            username VARCHAR(100) DEFAULT NULL,
                            blockeduserid INT(11) DEFAULT NULL,
                            blockeddate DATETIME DEFAULT CURRENT_TIMESTAMP,
                            blockeduserprofile LONGBLOB DEFAULT NULL,
                            PRIMARY KEY (blockedid),
                            FOREIGN KEY (userid) REFERENCES user(userid) ON DELETE CASCADE ON UPDATE CASCADE,
                            FOREIGN KEY (blockeduserid) REFERENCES user(userid) ON DELETE CASCADE ON UPDATE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                    """

                    await cursor.execute(create_user_blocked_table_query)
                    print("Table 'user_blocked' created successfully.")

                    
                    
                  
                    
                    
                    
                    
                    
                    
                    
                    create_passwordreset_table_query = """
                    CREATE TABLE IF NOT EXISTS passwordreset (
                        passwordresetid INT(11) NOT NULL AUTO_INCREMENT,
                        userid INT(11) NOT NULL,
                        emailaddress VARCHAR(1000) DEFAULT NULL,
                        code VARCHAR(100) NOT NULL,
                        expiredornot VARCHAR(100) NOT NULL,
                        sentdate DATETIME DEFAULT CURRENT_TIMESTAMP(),
                        PRIMARY KEY (passwordresetid),
                        KEY userid (userid),
                        CONSTRAINT passwordreset_ibfk_1 FOREIGN KEY (userid) REFERENCES user (userid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_passwordreset_table_query)
                    print("Table 'passwordreset' created successfully.")
                    
                    
                    
                    
                    
                    
                    
                    create_post_table_query = """
                    CREATE TABLE IF NOT EXISTS post (
                        postid INT(11) NOT NULL AUTO_INCREMENT,
                        userid INT(11) DEFAULT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        postdescription VARCHAR(1000) DEFAULT NULL,
                        groupname VARCHAR(1000) DEFAULT NULL,
                        posteddate DATETIME DEFAULT NULL,
                        posttype VARCHAR(50) DEFAULT NULL,
                        post LONGBLOB DEFAULT NULL,
                        userprofile LONGBLOB DEFAULT NULL,
                        filepath VARCHAR(1000) DEFAULT NULL,
                        textcolor VARCHAR(50) NOT NULL,
                        textbody VARCHAR(1000) NOT NULL,
                        popularcount INT(255) NOT NULL DEFAULT 0,
                        thelink VARCHAR(1000) NOT NULL,
                        groupid INT(11) DEFAULT NULL,
                        grouptype VARCHAR(100) DEFAULT NULL,
                        n_or_g VARCHAR(5) NOT NULL DEFAULT 'n',
                        PRIMARY KEY (postid),
                        KEY (userid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_post_table_query)
                    print("Table 'post' created successfully.")
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    create_post_like_table_query = """
                    CREATE TABLE IF NOT EXISTS post_like (
                        likeid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) DEFAULT NULL,
                        userid INT(11) DEFAULT NULL,
                        currentuserid INT(11) NOT NULL,
                        username VARCHAR(100) DEFAULT NULL,
                        profileimage LONGBLOB DEFAULT NULL,
                        PRIMARY KEY (likeid),
                        KEY postid (postid),
                        KEY userid (userid),
                        CONSTRAINT post_like_ibfk_1 FOREIGN KEY (postid) REFERENCES post (postid),
                        CONSTRAINT post_like_ibfk_2 FOREIGN KEY (userid) REFERENCES user (userid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_post_like_table_query)
                    print("Table 'post_like' created successfully.")
                    
                    
                    
                    
                    create_user_table_query = """
                    CREATE TABLE IF NOT EXISTS user (
                        userid INT(11) NOT NULL AUTO_INCREMENT,
                        username VARCHAR(100) DEFAULT NULL,
                        birthdate DATETIME DEFAULT NULL,
                        age INT(11) DEFAULT NULL,
                        emailaddress VARCHAR(100) DEFAULT NULL,
                        phonenumber VARCHAR(20) DEFAULT NULL,
                        profileimage LONGBLOB DEFAULT NULL,
                        createddate DATETIME DEFAULT NULL,
                        password VARCHAR(100) DEFAULT NULL,
                        onlinestatus INT(1) DEFAULT NULL,
                        emailauth TINYINT(4) NOT NULL DEFAULT 0,
                        notificationstatus TINYINT(4) NOT NULL DEFAULT 0,
                        PRIMARY KEY (userid)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_user_table_query)
                    print("Table 'user' created successfully.")
                    
                    
                    
                    
                    
                    
                    
                    create_favpost_table_query = """
                    CREATE TABLE IF NOT EXISTS favpost (
                        favpostid INT(11) NOT NULL AUTO_INCREMENT,
                        postid INT(11) NOT NULL,
                        userid INT(11) NOT NULL,
                        saveeddate DATETIME DEFAULT CURRENT_TIMESTAMP(),
                        PRIMARY KEY (favpostid),
                        KEY userid (userid),
                        KEY postid (postid),
                        CONSTRAINT favpost_ibfk_1 FOREIGN KEY (userid) REFERENCES user (userid) ON DELETE CASCADE,
                        CONSTRAINT favpost_ibfk_2 FOREIGN KEY (postid) REFERENCES post (postid) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
                     """

                    await cursor.execute(create_favpost_table_query)
                    print("Table 'favpost' created successfully.")




 
             
                    
                    
                    
                    
                    
                    
    except aiomysql.Error as e:
        print(f"Error creating tables: {e}")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="log-in")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
  


 
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta   
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=100000)
    to_encode.update({"exp": expire})  
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def verify_token(token: str, credentials_exception): 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        userid: str = payload.get("userid")
        if userid is None:
            raise credentials_exception  
        return userid
    except JWTError as e:
        raise credentials_exception



async def get_current_user(token: str = Depends(oauth2_scheme)): 
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,   
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)










async def get_user_by_id(selectedrepostpostowneruid: str):
    # Query to fetch username and emailaddress from the USER table
    query = "SELECT username, emailaddress FROM user WHERE userid = %s"

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (selectedrepostpostowneruid,))
                result = await cursor.fetchone()

                if result:
                    return result["username"], result["emailaddress"]
                else:
                    raise HTTPException(status_code=404, detail="User not found")

    except Exception as e:
        print(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user data")
    
    

@app.post("/report_post")
async def report_post(
    selectedOption: str = Form(...),
    selectedreportPostId: str = Form(...),
    selectedrepostpostowneruid: str = Form(...),
):
    sender_email = os.getenv("SMTP_USER")
    sender_name = "Ravoom"
    password = os.getenv("SMTP_PASS")
    formatted_sender = f"{sender_name} <{sender_email}>"
    additional_recipient = os.getenv("SMTP_USER")

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT username, emailaddress FROM user WHERE userid = %s", (selectedrepostpostowneruid,))
                result = await cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=404, detail="User not found")

                username, receiver_email = result["username"], result["emailaddress"]

    except Exception as e:
        print(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user data")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Report Submission Received"
    message["From"] = formatted_sender
    message["To"] = receiver_email  


    html = f"""
    <html>
      <head>
        <style>
          .btn-link {{
            background-color: rgb(43, 149, 236);
            color: #e0e0e0;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            transition: background-color 0.3s, color 0.3s;
          }}
          .btn-link:hover {{
            background-color: rgb(32, 121, 200);
            color: #e0e0e0;
          }}
        </style>
      </head>
      <body>
        <h1>Hey {username},</h1>
        <p>We've received a report for a post with the following details:</p>
        <ul>
          <li><strong>Report Option:</strong> {selectedOption}</li>
          <li><strong>Post ID:</strong> {selectedreportPostId}</li>
        </ul>
        <p>To view more details, visit your account by clicking the link below:</p>
        <p><a href="http://ravoom.com/home/comment/{selectedreportPostId}/n/home" class="btn-link">View Post</a></p>
        <p>Best Wishes,<br>Team Ravoom</p>
        <img src="cid:crabber_header" alt="Crabber Header" style="max-width: 40%; height: auto;"/>
      </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    image_path = "images/crabber_header.png"
    try:
        with open(image_path, 'rb') as img:
            img_data = img.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            image.add_header('Content-ID', '<crabber_header>')
            message.attach(image)
    except Exception as e:
        print(f"Error attaching image: {e}")

    try:
        context = ssl.create_default_context()  # Create a secure context
        with smtplib.SMTP(os.getenv("SMTP_HOST"), os.getenv("SMTP_PORT")) as server:
            server.starttls(context=context)  # Secure the connection with the context
            server.login(sender_email, password)
            recipients = [receiver_email, additional_recipient]
            server.sendmail(sender_email, recipients, message.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Error sending email")

    return JSONResponse(content={"message": "Report submitted successfully, email sent."}, status_code=200)
    
    
    
    
        
        
        
        
        
        
        
        
        
        
    




 
 
 
 
 
 


async def send_email(receiver_email: str, user_id: int,username:string):
 
    
    sender_email = os.getenv("SMTP_USER")
    sender_name = "Ravoom"
    password = os.getenv("SMTP_PASS")
    formatted_sender = f"{sender_name} <{sender_email}>"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Welcome to our service!"
    message["From"] = formatted_sender
    message["To"] = receiver_email

    html = f"""
    <html>
      <head>
        <style>
          .btn-link {{
            background-color: rgb(43, 149, 236);
            color: #e0e0e0;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            transition: background-color 0.3s, color 0.3s;
          }}
          .btn-link:hover {{
            background-color: rgb(32, 121, 200);
            color: #e0e0e0;
          }}
        </style>
      </head>
      <body>
        <h1>Hey {username},</h1>
        <p>Welcome to Ravoom – where conversations start, connections thrive, and communities grow! We’re excited to have you join our ever-growing network of curious minds, creators, and thinkers.</p>
        <p><strong>What to do next:</strong></p>
        <ul>
          <li><strong>Explore Topics:</strong> Dive into the discussions that matter to you. From [Topic A] to [Topic B], there’s a community waiting for your voice.</li>
          <li><strong>Follow Interesting People:</strong> Find and follow users who inspire you. Whether it’s trending insights, niche content, or everyday conversations, there’s always something happening.</li>
          <li><strong>Share Your Thoughts:</strong> Have something to say? Post your own thoughts, photos, or ideas, and watch the conversation unfold.</li>
        </ul>
        <p>At Ravoom, you can:</p>
        <ul>
          <li>Connect with like-minded individuals</li>
          <li>Engage in real-time discussions</li>
          <li>Discover trending topics and communities</li>
        </ul>
        <p>Your profile is ready – so jump in and start exploring. The best conversations are just a click away and say bye to Karma!</p>
        
        <p><a href="http://ravoom.com/auth/email-auth/{user_id}" class="btn-link">Confirm Email</a></p>
        <p>Best Wishes,<br>Team Ravoom</p>
        
          <img src="cid:crabber_header" alt="Crabber Header" style="max-width: 40%; height: auto;"/>
          
          
      </body>
    </html>
    """
    

    part = MIMEText(html, "html")

    message.attach(part)
    
    
    image_path = "images/crabber_header.png"  
    with open(image_path, 'rb') as img:
        img_data = img.read()
        image = MIMEImage(img_data, name=os.path.basename(image_path))
        image.add_header('Content-ID', '<crabber_header>')
        message.attach(image)
        

    context = ssl.create_default_context()  # Create a secure context
    with smtplib.SMTP(os.getenv("SMTP_HOST"), os.getenv("SMTP_PORT")) as server:
        server.starttls(context=context)  # Secure the connection with the context
        server.login(sender_email, password)
        recipients = [receiver_email]
        server.sendmail(sender_email, recipients, message.as_string())
        
#   recipients = [receiver_email, additional_recipient]     
 
def generate_random_user_id(length=9):
    if length > 9:
        raise ValueError("Maximum length for INT is 11 digits")
    
    min_value = 10**(length - 1)
    max_value = 10**length - 1
    return random.randint(min_value, max_value)

    
@app.post("/sign-up")
async def sign_up(
    username: str = Form(...),
    birthdate: str = Form(...),
    age: int = Form(...),
    emailaddress: str = Form(...),
    phonenumber: str = Form(...),
    password: str = Form(...),  
    reenterpassword: str = Form(...),
    profileimage: UploadFile = File(...)
):
    if password != reenterpassword:
        return JSONResponse(content={"message": "Passwords do not match"}, status_code=400)
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_email_query = "SELECT COUNT(*) FROM user WHERE emailaddress = %s"
                await cursor.execute(check_email_query, (emailaddress,))
                result = await cursor.fetchone()
                if result[0] > 0:
                    return JSONResponse(content={"message": "Email address already exists"}, status_code=400)

                createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                onlinestatus = 0 
                image_data = await profileimage.read()
                user_id = generate_random_user_id()
               

                insert_query = """
                INSERT INTO user (userid, username, birthdate, age, emailaddress, phonenumber, profileimage, createddate, password, onlinestatus)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(insert_query, (user_id, username, birthdate, age, emailaddress, '000000000', image_data, createddate, password, onlinestatus))
                
                await conn.commit()

        await send_email(emailaddress, user_id, username)
        return JSONResponse(content={"message": "User created successfully", "userid": user_id}, status_code=201)

    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Server error")





@app.post("/sign-up-with-google")
async def sign_up_with_google(
    username: str = Form(...),
    birthdate: str = Form(...),
    emailaddress: str = Form(...),
    profileimage: str = Form(...),   
):
    try:
        print(f"Received data: username={username}, birthdate={birthdate}, emailaddress={emailaddress}, profileimage={profileimage}")

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_email_query = "SELECT COUNT(*) FROM user WHERE emailaddress = %s"
                await cursor.execute(check_email_query, (emailaddress,))
                result = await cursor.fetchone()

                if result[0] > 0:
                    # Email already exists
                    print(f"Email {emailaddress} already exists.")
                    return JSONResponse(content={"message": "Email address already exists"}, status_code=400)

                createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                onlinestatus = 0
                user_id = generate_random_user_id()

                image_data = None
                if profileimage.startswith("http"):  
                    print(f"Fetching image from URL: {profileimage}")
                    try:
                        image_data = await fetch_image_from_url(profileimage)
                    except Exception as e:
                        print(f"Error fetching image: {e}")
                        raise HTTPException(status_code=400, detail="Failed to fetch image from URL")
                else:   
                    try:
                        image_data = base64.b64decode(profileimage.split(',')[1])   
                    except Exception as e:
                        print(f"Error decoding base64 image: {e}")
                        raise HTTPException(status_code=400, detail="Invalid base64 image data")
                
                insert_query = """
                INSERT INTO user (userid, username, birthdate, age, emailaddress, phonenumber, profileimage, createddate, password, onlinestatus)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(insert_query, (user_id, username, birthdate, 0, emailaddress, '0775004178', image_data, createddate, 'awfwfa', onlinestatus))
                await conn.commit()

        return JSONResponse(content={"message": "User created successfully", "userid": user_id}, status_code=201)

    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Server error")




async def fetch_image_from_url(url: str) -> bytes:
    """Fetches an image from a URL and returns the binary data"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                print(f"Successfully fetched image from URL: {url}")
                return response.content   
            else:
                print(f"Failed to fetch image. Status code: {response.status_code}, URL: {url}")
                raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching image from URL: {url}, Error: {e}")
        raise HTTPException(status_code=400, detail="Error fetching image from URL")
    
    
    
    
    










def generate_random_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def send_email_password_reset(username: str,receiver_email: str, code: str):
    sender_email = os.getenv("SMTP_USER")
    sender_name = "Ravoom"
    password = os.getenv("SMTP_PASS")
    formatted_sender = f"{sender_name} <{sender_email}>"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset"
    message["From"] = formatted_sender
    message["To"] = receiver_email

    html = f"""
    <html>
      <body>
        <h1>Hi {username},</h1>
        <p>It looks like you requested to reset your password for your Ravoom account. Don’t worry, we’ve got you covered!</p>
        <p>Your reset code is:</p>
        <p style="font-size: 50px; font-weight: bold;">{code}</p>
        <p>If you didn’t request this, you can safely ignore this email – your password will remain unchanged.</p>
        <p>For security reasons, the reset link will expire in 60 seconds. If you need further assistance, feel free to reach out to our support team.</p>
        <p>Thank you for being part of the Ravoom community!</p>
        <p>Stay connected,<br>The Ravoom Team</p>
        
        <img src="cid:crabber_header" alt="Crabber Header" style="max-width: 40%; height: auto;"/>
      </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    context = ssl.create_default_context()  # Create a secure context
    with smtplib.SMTP(os.getenv("SMTP_HOST"), os.getenv("SMTP_PORT")) as server:
        server.starttls(context=context)  # Secure the connection with the context
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

@app.post("/check-password-for-reset")
async def check_password_for_reset(
    userid: str = Form(...),
    curruntpassword: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                check_curruntuser_password = """
                    SELECT password, emailaddress,username FROM user WHERE userid = %s
                """
                await cursor.execute(check_curruntuser_password, (userid,))
                admin_result = await cursor.fetchone()

                if not admin_result:
                    return JSONResponse(status_code=404, content={"message": "User not found"})

                databasepassword = admin_result['password']
                useremailaddress = admin_result['emailaddress']
                username = admin_result['username']

                if curruntpassword == databasepassword:
                    code = generate_random_code()
                    insert_code = """
                        INSERT INTO passwordreset (userid, emailaddress, code, expiredornot, sentdate) 
                        VALUES (%s, %s, %s, %s, NOW())
                    """
                    await cursor.execute(insert_code, (userid, useremailaddress, code, '0'))
                    await conn.commit()

                    get_passwordreset_id = """
                        SELECT passwordresetid FROM passwordreset 
                        WHERE userid = %s 
                        ORDER BY sentdate DESC LIMIT 1
                    """
                    await cursor.execute(get_passwordreset_id, (userid,))
                    passwordreset_result = await cursor.fetchone()

                    await send_email_password_reset(username,useremailaddress, code)

                    return {"message": "matched", "emailaddress": useremailaddress, "code": code, "passwordresetid": passwordreset_result['passwordresetid']}
                else:
                    return {"message": "notmatched"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    












@app.post("/expire-password")
async def expire_password(
    userid: str = Form(...),
    passwordresetid: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                markthe_expire_of_code = """
                    UPDATE passwordreset SET expiredornot = %s WHERE userid = %s AND passwordresetid = %s
                """
                await cursor.execute(markthe_expire_of_code, (1, userid, passwordresetid))
                await conn.commit()

                return {"message": "expired"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
@app.post("/expire-forget-password")
async def expire_forget_password(
    userid: str = Form(...),
    forgetpasswordtid: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                markthe_expire_of_code = """
                    UPDATE forgetpassword SET expiredornot = %s WHERE userid = %s AND forgetpasswordtid = %s
                """
                await cursor.execute(markthe_expire_of_code, (1, userid, forgetpasswordtid))
                await conn.commit()

                return {"message": "expired"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    

   
blacklist = set()

def add_to_blacklist(token: str):
    blacklist.add(token)
    
    
@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    add_to_blacklist(token)  
    return JSONResponse(
        content={"message": "Logged out successfully"},
        status_code=200
    )
    
    
    









    
    

@app.post("/update-new-password")
async def update_new_password(
    userid: str = Form(...),
    newpassword: str = Form(...),
    useremailaddress: str = Form(...),
    reenternewpassword: str = Form(...),
    current_user: str = Depends(get_current_user)
 
     
):
    try:
        
        if str(current_user) != userid:
           raise HTTPException(status_code=401, detail="Unauthorized access")
       
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
            
                update_password = """
                    UPDATE user SET password = %s WHERE userid = %s  
                """
                await cursor.execute(update_password, (newpassword, userid))
                await conn.commit()

            
                await send_email_password_reset_successfully("aaaaaaaaaaaaaa" , useremailaddress)

                return {"message": "updated"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

async def send_email_password_reset_successfully(receiver_email: str,username: str):
    try:
        sender_email = os.getenv("SMTP_USER")
        sender_name = "Ravoom"
        password = os.getenv("SMTP_PASS")
        formatted_sender = f"{sender_name} <{sender_email}>"

        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Ravoom Password Has Been Successfully Reset"
        message["From"] = formatted_sender
        message["To"] = receiver_email

        html = f"""
        <html>
          <body>
            <h2>Hi {username},</h2>
            <p>We wanted to let you know that your password for your Ravoom account was successfully reset. You can now log in with your new password and continue enjoying all the features Ravoom has to offer.</p>
            <p>If you did not request this password change, please contact our support team immediately for further assistance. We’re here to help!</p>
            <p>For added security, we recommend regularly updating your password and ensuring that it’s strong and unique.</p>
            <p>Thanks for being part of the Ravoom community!</p>
            <p>Best regards,<br>Team Ravoom</p>
            
            <img src="cid:crabber_header" alt="Crabber Header" style="max-width: 40%; height: auto;"/>
            
          </body>
        </html>
        """

        part = MIMEText(html, "html")
        message.attach(part)

        context = ssl.create_default_context()  # Create a secure context
        with smtplib.SMTP(os.getenv("SMTP_HOST"), os.getenv("SMTP_PORT")) as server:
            server.starttls(context=context)  # Secure the connection with the context
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

    except Exception as e:
        print(f"Error sending email: {e}")
    
    
    
    
    
    
    
    
    
    
    









@app.post("/update-forget-new-password")
async def update_forget_new_password(
    userid: str = Form(...),
    newpassword: str = Form(...),
    useremailaddress: str = Form(...),
    reenternewpassword: str = Form(...),
   
):
    try:
     
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                get_user_query = """
                    SELECT username FROM user WHERE userid = %s
                """
                await cursor.execute(get_user_query, (userid,))
                user_result = await cursor.fetchone()
                
                if not user_result:
                    raise HTTPException(status_code=404, detail="User not found")
                
                username = user_result['username']
                
                update_password = """
                    UPDATE user SET password = %s WHERE userid = %s
                """
                await cursor.execute(update_password, (newpassword, userid))
                await conn.commit()
                
                # Send email notification
                await send_email_password_reset_successfully(useremailaddress, username)
                
                return {"message": "Password updated successfully"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/update_online_status")
async def update_online_status(
    userid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                update_status_query = """
                    UPDATE user SET onlinestatus = %s WHERE userid = %s  
                """
                await cursor.execute(update_status_query, (1, userid))
                await conn.commit()

                return {"message": "User status updated successfully"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
@app.post("/update_online_status_hidden")
async def update_online_status_hidden(
    userid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                update_status_query = """
                    UPDATE user SET onlinestatus = %s WHERE userid = %s  
                """
                await cursor.execute(update_status_query, (0, userid))
                await conn.commit()

                return {"message": "User status updated successfully"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    

 
    
    
    
    




@app.post("/check_postowner_online_status")
async def check_postowner_online_status(
    userid: str = Form(...),
):
    try: 
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = "SELECT onlinestatus FROM user WHERE userid = %s"
                await cursor.execute(query, (userid,))
                result = await cursor.fetchone()
                print(f"result['onlinestatus']result['onlinestatus'] error: {result['onlinestatus']}")
                
                if result:
                    if result['onlinestatus'] == 0:
                        return {"message": "offline"}
                    else:
                        return {"message": "online"}
                else:
                    return {"message": "user not found"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
      
    
    
    
    
@app.post("/code-check")
async def code_check(
    userid: str = Form(...),
    passwordresetid: str = Form(...),
    code: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                check_code_query = """
                    SELECT code, expiredornot FROM passwordreset 
                    WHERE userid = %s AND passwordresetid = %s
                """
                await cursor.execute(check_code_query, (userid, passwordresetid))
                result = await cursor.fetchone()
 
                if not result:
                    return JSONResponse(status_code=404, content={"message": "Code not found"})

                if result['code'] != code:
                    return {"message": "notmatched"}

                if result['expiredornot'] == '1':
                    return {"message": "expired"}

             
                update_expiredornot_query = """
                    UPDATE passwordreset SET expiredornot = '1' 
                    WHERE userid = %s AND passwordresetid = %s
                """
                await cursor.execute(update_expiredornot_query, (userid, passwordresetid))
                await conn.commit()

                return {"message": "matched"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    















    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/check-code-submit-forget-password")
async def check_code_submit_forget_password(
    userid: str = Form(...),
    forgetpasswordtid: str = Form(...),
    code: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                check_code_query = """
                    SELECT code, forgetpasswordtid,expiredornot,code FROM forgetpassword 
                    WHERE userid = %s AND forgetpasswordtid = %s
                """
                await cursor.execute(check_code_query, (userid, forgetpasswordtid))
                result = await cursor.fetchone()
 
                if not result:
                    return JSONResponse(status_code=404, content={"message": "Code not found"})

                if result['code'] != code:
                    return {"message": "notmatched"}

                if result['expiredornot'] == '1':
                    return {"message": "expired"}

             
                update_expiredornot_query = """
                    UPDATE forgetpassword SET expiredornot = '1' 
                    WHERE userid = %s AND forgetpasswordtid = %s
                """
                await cursor.execute(update_expiredornot_query, (userid, forgetpasswordtid))
                await conn.commit()

                return {"message": "matched"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    

def generate_random_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def is_valid_email(email: str) -> bool:
    email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(email_regex, email) is not None

async def send_email_forget_password(receiver_email: str, username: str, code: str):
    if not is_valid_email(receiver_email):
        raise ValueError("Invalid email address")

    sender_email = os.getenv("SMTP_USER")
    sender_name = "Ravoom"
    password = os.getenv("SMTP_PASS")
    formatted_sender = f"{sender_name} <{sender_email}>"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset Your Ravoom Password"
    message["From"] = formatted_sender
    message["To"] = receiver_email

    reset_link = f"http://ravoom.com/reset-password/"

    html = f"""
    <html>
      <body>
        <h1>Hi {username},</h1>
        <p>It looks like you requested to reset your password for your Ravoom account. Don’t worry, we’ve got you covered!</p>
        <p>Your reset code is:</p>
        <p style="font-size: 50px; font-weight: bold;">{code}</p>
        <p>Click the button below to reset your password:</p>
        <p><a href="{reset_link}" style="
          background-color: rgb(43, 149, 236);
          color: white;
          padding: 10px 20px;
          text-decoration: none;
          border-radius: 20px;
          font-weight: bold;
          display: inline-block;
          transition: background-color 0.3s, color 0.3s;
        ">Reset Password</a></p>
        <p>If you didn’t request this, you can safely ignore this email – your password will remain unchanged.</p>
        <p>For security reasons, the reset link will expire in 60 seconds. If you need further assistance, feel free to reach out to our support team.</p>
        <p>Thank you for being part of the Ravoom community!</p>
        <p>Stay connected,<br>The Ravoom Team</p>
        
        <img src="cid:crabber_header" alt="Crabber Header" style="max-width: 40%; height: auto;"/>
      </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    context = ssl.create_default_context()  # Create a secure context
    with smtplib.SMTP(os.getenv("SMTP_HOST"), os.getenv("SMTP_PORT")) as server:
        server.starttls(context=context)  # Secure the connection with the context
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

@app.post("/check-email-address-exist")
async def check_email_address_exist(
    emailaddress: str = Form(...),
):
    try:
        if not is_valid_email(emailaddress):
            return {"message": "Invalid email format"}

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                check_user_query = """
                    SELECT userid, username FROM user WHERE emailaddress = %s
                """
                await cursor.execute(check_user_query, (emailaddress,))
                user_result = await cursor.fetchone()
                
                if not user_result:
                    return {"message": "noemail"}

                userid = user_result['userid']
                username = user_result['username']
                code = generate_random_code()

                insert_forget_password_query = """
                    INSERT INTO forgetpassword (userid, code, expiredornot, emailaddress, sentdate) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                await cursor.execute(insert_forget_password_query, (userid, code, '0', emailaddress, datetime.now()))
                forgetpasswordtid = cursor.lastrowid
                await conn.commit()

                await send_email_forget_password(emailaddress, username, code)

                return {"message": "Code sent successfully", "forgetpasswordtid": forgetpasswordtid, "userid": userid, "code": code, "emailaddress": emailaddress}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except ValueError as e:
        print(f"Value error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/create-group")
async def create_group(
    userid: str = Form(...),
    grouptype: str = Form(...),
    groupname: str = Form(...),
    groupimage: UploadFile = File(...),
    groupbackgroundimage: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    try:
        if str(current_user) != userid:
            raise HTTPException(status_code=401, detail="Unauthorized access")

        createdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        groupbackgroundimage_data = await groupbackgroundimage.read()
        groupimage_data = await groupimage.read()

        async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    insert_group_query = """
                    INSERT INTO groups (groupownerid, groupname, grouptype, groupimage, groupbackgroundimage, createdate)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    await cursor.execute(insert_group_query, (userid, groupname, grouptype, groupimage_data, groupbackgroundimage_data, createdate))
                    await conn.commit()

                    await cursor.execute("SELECT LAST_INSERT_ID() AS groupid")
                    groupid_row = await cursor.fetchone()
                    if not groupid_row:
                        raise HTTPException(status_code=500, detail="Failed to retrieve group ID")
                    groupid = groupid_row["groupid"]

                    await cursor.execute("SELECT * FROM user WHERE userid = %s", (userid,))
                    user_row = await cursor.fetchone()
                    if not user_row:
                        raise HTTPException(status_code=404, detail="User not found")

                    profileimage = user_row["profileimage"]
                    username = user_row["username"]

                    insert_group_user_query = """
                    INSERT INTO group_users (groupid, userid, profileimage, username, usertype, joined_date)
                    VALUES (%s, %s, %s, %s, 'admin', %s)
                    """
                    await cursor.execute(insert_group_user_query, (groupid, userid, profileimage, username, createdate))
                    await conn.commit()

                    insert_group_member_count_query = """
                    INSERT INTO groupmembercount (groupid, groupownerid, grouptype, groupname, groupimage, members)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    await cursor.execute(insert_group_member_count_query, (groupid, userid, grouptype, groupname, groupimage_data, 1))
                    await conn.commit()

                    letter_string = generate_random_letter_string()
                    post_id = generate_combined_post_id(letter_string)

                    insert_init_post_query = """
                    INSERT INTO post (postid, userid, username, groupname, posteddate, posttype, post, userprofile, groupid, grouptype, n_or_g)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    await cursor.execute(insert_init_post_query, (post_id, userid, username, groupname, createdate, 'group', groupbackgroundimage_data, profileimage, groupid, grouptype, 'n'))
                    await conn.commit()
            

        return JSONResponse(content={"groupid": groupid, "message": "Group created successfully"}, status_code=201)

    except aiomysql.MySQLError as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/join-group")
async def join_group(
    userid: str = Form(...),
    groupid: str = Form(...),
):
    try:
        joined_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:

                await cursor.execute("SELECT * FROM user WHERE userid = %s", (userid,))
                user_row = await cursor.fetchone()
                
                if not user_row:
                    raise HTTPException(status_code=404, detail="User not found")

                profileimage = user_row["profileimage"]
                username = user_row["username"]

                await cursor.execute(
                    "SELECT * FROM group_users WHERE groupid = %s AND userid = %s",
                    (groupid, userid)
                )
                group_user_row = await cursor.fetchone()
                
                if group_user_row:
                    delete_group_user_query = """
                    DELETE FROM group_users
                    WHERE groupid = %s AND userid = %s
                    """
                    await cursor.execute(delete_group_user_query, (groupid, userid))
                
                await cursor.execute(
                    "SELECT * FROM iamfollowing WHERE myuserid = %s AND groupid = %s AND type = 'group'",
                    (userid, groupid)
                )
                existing_following_record = await cursor.fetchone()
                
                if existing_following_record:
                    delete_following_query = """
                    DELETE FROM iamfollowing
                    WHERE myuserid = %s AND groupid = %s AND type = 'group'
                    """
                    await cursor.execute(delete_following_query, (userid, groupid))
                    
                    await cursor.execute("SELECT members FROM groupmembercount WHERE groupid = %s", (groupid,))
                    existing_group = await cursor.fetchone()

                    if existing_group:
                        # If groupid exists, decrement the members count by 1
                        update_group_member_count_query = """
                        UPDATE groupmembercount
                        SET members = members - 1
                        WHERE groupid = %s
                        """
                        await cursor.execute(update_group_member_count_query, (groupid,))
                        
                
                if group_user_row or existing_following_record:
                    await conn.commit()   
                    return JSONResponse(content={"groupid": groupid, "message": "User removed from the group and unfollowed"}, status_code=200)

                insert_group_user_query = """
                INSERT INTO group_users (groupid, userid, profileimage, username, usertype, joined_date)
                VALUES (%s, %s, %s, %s, 'user', %s)
                """
                await cursor.execute(
                    insert_group_user_query,
                    (groupid, userid, profileimage, username, joined_date)
                )
                
                insert_user_into_following_query = """
                INSERT INTO iamfollowing (myuserid, otheruserid, username, profile, date, type, groupid)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(
                    insert_user_into_following_query,
                    (userid, None, username, None, joined_date, 'group', groupid)
                )
                
                await conn.commit()  
                
                
                await cursor.execute("SELECT members FROM groupmembercount WHERE groupid = %s", (groupid,))
                existing_group = await cursor.fetchone()

                if existing_group:
                    # If groupid exists, increment the members count by 1
                    update_group_member_count_query = """
                    UPDATE groupmembercount
                    SET members = members + 1
                    WHERE groupid = %s
                    """
                    await cursor.execute(update_group_member_count_query, (groupid,))


        return JSONResponse(content={"groupid": groupid, "message": "User joined group successfully"}, status_code=201)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
  









@app.post("/change_user_type_in_group")
async def change_user_type_in_group(
    userid: str = Form(...),
    groupid: str = Form(...),
    usertype: str = Form(...),
    curruntuserid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                update_group_user_query = """
                UPDATE group_users SET usertype = %s
                WHERE groupid = %s AND userid = %s
                """
                await cursor.execute(
                    update_group_user_query,
                    (usertype, groupid, userid)
                )

                check_admin_query = """
                SELECT usertype FROM group_users
                WHERE groupid = %s AND userid = %s
                """
                await cursor.execute(check_admin_query, (groupid, curruntuserid))
                admin_result = await cursor.fetchone()

                if admin_result and admin_result['usertype'] == 'admin' and usertype != 'mod':
                    await cursor.execute(
                        update_group_user_query,
                        ('user', groupid, curruntuserid)
                    )

                await conn.commit()

        return {"message": f"User {userid} updated to {usertype} in group {groupid}"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    







    
    
    
    
    
    
    
    
    
    
@app.post("/remove-user-from-group")
async def remove_user_from_group(
    userid: str = Form(...),
    groupid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                remove_user_query = """
                DELETE FROM group_users
                WHERE groupid = %s AND userid = %s
                """
                await cursor.execute(
                    remove_user_query,
                    (groupid, userid)
                )

                await conn.commit()

        return {"message": f"User {userid} removed from group {groupid}"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    






@app.post("/remove_replay_comment")
async def remove_replay_comment(
    commentreplayid: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                remove_user_query = """
                DELETE FROM commentreply
                WHERE commentreplayid = %s 
                """
                await cursor.execute(
                    remove_user_query,
                    (commentreplayid)
                )

                await conn.commit()

        return {"message": "deleted"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
        
    
    
    
    
@app.post("/remove-group")
async def remove_group(
    groupid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
              
                fetch_post_ids = """
                SELECT postid FROM grouppost
                WHERE groupid = %s
                """
                await cursor.execute(fetch_post_ids, (groupid,))
                post_ids = await cursor.fetchall()
                post_ids = [post['postid'] for post in post_ids]

               
                if post_ids:
                    remove_images_of_post = """
                    DELETE FROM groupimage
                    WHERE postid IN %s
                    """
                    await cursor.execute(remove_images_of_post, (post_ids,))
                
              
                remove_group_posts = """
                DELETE FROM grouppost
                WHERE groupid = %s
                """
                await cursor.execute(remove_group_posts, (groupid,))
                
         
                remove_group = """
                DELETE FROM groups
                WHERE groupid = %s
                """
                await cursor.execute(remove_group, (groupid,))
                
                remove_groupmembercount = """
                DELETE FROM groupmembercount
                WHERE groupid = %s
                """
                await cursor.execute(remove_groupmembercount, (groupid,))
                
                
                
                
                await conn.commit()

        return {"message": "removed"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/update-backgroundimage")
async def update_backgroundimage(
    groupid: str = Form(...),
    backgroundimage: UploadFile = File(...)
):
    try:
        backgroundimage_data = await backgroundimage.read()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                fetch_group_image = """
                SELECT groupimage FROM groups
                WHERE groupid = %s
                """
                await cursor.execute(fetch_group_image, (groupid,))
                group_image = await cursor.fetchone()
                groupbackgroundimageupdateddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                if group_image:
                    group_image_data = group_image['groupimage']

                    update_background_image = """
                    UPDATE groups
                    SET groupbackgroundimage = %s, groupimage = %s,groupbackgroundimageupdateddate=%s
                    WHERE groupid = %s
                    """
                    await cursor.execute(update_background_image, (backgroundimage_data, group_image_data, groupbackgroundimageupdateddate,groupid))
                
                await conn.commit()

        return {"message": "done"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
   
   
    
@app.post("/update-groupmainimage")
async def update_groupmainimage(
    groupid: str = Form(...),
    groupmainimage: UploadFile = File(...)
):
    try:
        groupmainimage_data = await groupmainimage.read()

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                fetch_group_image = """
                SELECT groupimageupdateddate,groupbackgroundimage FROM groups
                WHERE groupid = %s
                """
                await cursor.execute(fetch_group_image, (groupid,))
                group_image = await cursor.fetchone()
                groupimageupdateddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                

                if group_image:
                    group_image_data = group_image['groupbackgroundimage']

                    update_background_image = """
                    UPDATE groups
                    SET  groupbackgroundimage = %s, groupimage = %s,groupimageupdateddate =%s
                    WHERE groupid = %s
                    """
                    await cursor.execute(update_background_image, (group_image_data, groupmainimage_data,groupimageupdateddate, groupid))
                
                await conn.commit()

        return {"message": "done"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    






@app.post("/update-user-profile")
async def update_user_profile(
    userid: str = Form(...),
    profileimage: UploadFile = File(...),
):
    try:
        profileimage_data = await profileimage.read()

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                update_profile_image = """
                UPDATE user
                SET profileimage = %s
                WHERE userid = %s
                """
                await cursor.execute(update_profile_image, (profileimage_data, userid))

                update_post_user_profile = """
                UPDATE post
                SET userprofile = %s
                WHERE userid = %s
                """
                await cursor.execute(update_post_user_profile, (profileimage_data, userid))

                await conn.commit()

        return {"message": "done"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
      
    
    
    
    
@app.post("/update-groupinformation")
async def update_groupinformation(
    groupid: str = Form(...),
    groupname: str = Form(...),
):
    try:
    
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                fetch_group_image = """
                SELECT groupbackgroundimage, groupimage FROM groups
                WHERE groupid = %s
                """
                await cursor.execute(fetch_group_image, (groupid,))
                group_image = await cursor.fetchone()

                if group_image:
                    group_backgroundimage_data = group_image['groupbackgroundimage']
                    group_image_data = group_image['groupimage']

                    update_group_info = """
                    UPDATE groups
                    SET groupbackgroundimage = %s, groupimage = %s, groupname = %s
                    WHERE groupid = %s
                    """
                    await cursor.execute(update_group_info, (group_backgroundimage_data, group_image_data, groupname, groupid))
                    
                    
                    update_group_info_post_table = """
                    UPDATE post
                    SET groupname = %s 
                    WHERE groupid = %s
                    """
                    await cursor.execute(update_group_info_post_table, (groupname, groupid))
                    
                    
                    
                    
                    update_group_info_groupnumber_table = """
                    UPDATE groupmembercount
                    SET groupname = %s 
                    WHERE groupid = %s
                    """
                    await cursor.execute(update_group_info_groupnumber_table, (groupname, groupid))
                    
                    
                
                await conn.commit()

        return {"message": "done"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
 
 
    
@app.post("/accept-user-from-group")
async def accept_user_from_group(
    userid: str = Form(...),
    groupid: str = Form(...),
    groupownerid: str = Form(...),
    groupname: str = Form(...),
):
    try:
        createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                update_user_status_query = """
                UPDATE group_users
                SET status = 1
                WHERE groupid = %s AND userid = %s
                """
                await cursor.execute(
                    update_user_status_query,
                    (groupid, userid)
                )
                
                await cursor.execute(
                    """ 
                    SELECT username, profileimage FROM user WHERE userid = %s
                    """,
                    (userid,)
                )
                user_info = await cursor.fetchone()
                if not user_info:
                    raise HTTPException(status_code=404, detail="User not found")
                
                username = user_info['username']
                profileimage = user_info.get('profileimage', None)
                
                insert_notification_query = """
                INSERT INTO notification (
                    postowneruserid, myuserid, username, notificationtype, commenttext,
                    date, userprofile, seenstatus,groupid,groupname
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s,%s)
                """
                await cursor.execute(
                    insert_notification_query,
                    (
                       userid ,  groupownerid, username, 'grouppermission', f'your request is accepted for group {groupname}',
                        createddate, profileimage, 0,groupid,groupname
                    )
                )
                
                await cursor.execute("""
                    UPDATE user
                    SET notificationstatus = 1
                    WHERE userid = %s
                """, (userid,))
                
                

                await conn.commit()

        return {"message": f"User {userid} status updated to 1 in group {groupid}"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/get_curruntuser_detail_from_group")
async def get_curruntuser_detail_from_group(
    userid: str = Form(...),
    groupid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                get_user_detail_query = """
                SELECT usertype FROM group_users
                WHERE groupid = %s AND userid = %s
                """
                await cursor.execute(
                    get_user_detail_query,
                    (groupid, userid)
                )
                
                user_detail = await cursor.fetchone()
                
                if user_detail:
                    return {"usertype": user_detail["usertype"]}
                else:
                    return {"message": "User not found in group"}, 404

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
@app.post("/update-email-confirmation")
async def update_email_confirmation(userid: str = Form(...)):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                update_user_query = """
                UPDATE user SET emailauth = %s
                WHERE userid = %s
                """
                await cursor.execute(update_user_query, (1, userid))
                await conn.commit()

        return JSONResponse(content={"message": "Email confirmation updated successfully"}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/add_iamfollowed_users_into_group")
async def add_iamfollowed_users_into_group(
    groupid: str = Form(...),
    userid: str = Form(...),
):
    try:
        createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                select_user_query = """
                SELECT username, profileimage FROM user WHERE userid = %s
                """
                await cursor.execute(select_user_query, (userid,))
                user_info = await cursor.fetchone()

                if not user_info:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user_info['username']
                profileimage = user_info['profileimage']

                insert_query = """
                INSERT INTO group_users (groupid, userid, username, profileimage, usertype, joined_date, status)
                VALUES (%s, %s, %s, %s, %s, NOW(), 1)
                """
                await cursor.execute(
                    insert_query,
                    (groupid, userid, username, profileimage, 'user')
                )

                insert_notification_query = """
                INSERT INTO notification (
                    postowneruserid, myuserid , username, notificationtype, commenttext, date, userprofile, seenstatus, groupid
                ) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(
                    insert_notification_query,
                    (userid,'5', username, 'grouppermission', 'you are added to a group', createddate, profileimage, 0, groupid)
                )

                await conn.commit()

        return {"message": "User added to group successfully"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
 
    

    
    
    
    
    
    
    
    
 
    
    
@app.post("/search-follower-users")
async def search_follower_users(
    groupid: str = Form(...),
    username: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                get_user_detail_query = """
                SELECT * FROM group_users
                WHERE groupid = %s AND username LIKE %s
                """
                await cursor.execute(get_user_detail_query, (groupid, f"%{username}%"))
                user_details = await cursor.fetchall()

                if not user_details:
                    return {"message": "No users found"}  

            
                for user in user_details:
                    if user['profileimage']:
                        user['profileimage'] = base64.b64encode(user['profileimage']).decode('utf-8')
                    else:
                        user['profileimage'] = None  

                return user_details

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/remove-user-from-iamfollowing")
async def remove_user_from_iamfollowing(
    myuid: str = Form(...),
    otheruserid: str = Form(...),
):
    try:
       
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                delete_query = """
                DELETE FROM iamfollowing WHERE myuserid = %s AND otheruserid = %s AND type = 'user'
                """
                await cursor.execute(delete_query, (myuid, otheruserid))
                
                delete_query_iamfollowed = """
                DELETE FROM iamfollowed WHERE myuserid = %s AND otheruserid = %s
                """
                await cursor.execute(delete_query_iamfollowed, (otheruserid , myuid ))
                
                await conn.commit()

                return {"message": "removed"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/check-isa-member-of-group")
async def check_isa_member_of_group(
    userid: str = Form(...),
    groupid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
   
                get_user_detail_query = """
                SELECT * FROM group_users
                WHERE userid = %s AND groupid = %s
                """
                await cursor.execute(
                    get_user_detail_query,
                    (userid, groupid)
                )
                
                user_record = await cursor.fetchone()

         
                if user_record:
                    return JSONResponse(content={"message": "yes"}, status_code=200)
                else:
                    return JSONResponse(content={"message": "no"}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/change_user_type_mod_into_user")
async def change_user_type_mod_into_user(
    groupid: str = Form(...),
    curruntuserid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                update_group_user_query = """
                UPDATE group_users SET usertype = %s
                WHERE groupid = %s AND userid = %s
                """
                await cursor.execute(
                    update_group_user_query,
                    ('user', groupid, curruntuserid)
                )
                
                await conn.commit()
                
                return {"message": f"User type updated {curruntuserid} in group {groupid}"}

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
@app.post("/search-all-users")
async def search_all_users(
    username: str = Form(...),
    groupid: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                get_user_detail_query = """
                SELECT iamfollowed.otheruserid, iamfollowed.username, iamfollowed.profile 
                FROM iamfollowed
                WHERE  iamfollowed.username LIKE %s
                AND iamfollowed.otheruserid NOT IN (
                    SELECT userid FROM group_users WHERE groupid = %s
                )
                """
                await cursor.execute(get_user_detail_query, ( f"%{username}%", groupid))
                user_details = await cursor.fetchall()

                if not user_details:
                    return {"message": "No users found"}  

                for user in user_details:
                    if user['profile']:
                        user['profile'] = base64.b64encode(user['profile']).decode('utf-8')
                    else:
                        user['profile'] = None  

                return user_details

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    

@app.post("/get_curruntuser_is_followed_list")
async def get_curruntuser_is_followed_list(
    userid: str = Form(...),
    groupid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
        
                get_user_detail_query = """
                SELECT iamfollowed.otheruserid, iamfollowed.username, iamfollowed.profile FROM iamfollowed
                WHERE iamfollowed.myuserid = %s
                AND iamfollowed.otheruserid NOT IN (
                    SELECT userid FROM group_users WHERE groupid = %s
                )
                """
                await cursor.execute(get_user_detail_query, (userid, groupid))
                user_details = await cursor.fetchall()
                
                if not user_details:
                    return {"message": "No users found"}, 404
                
                for user in user_details:
                    if user['profile']:
                        profile_image_base64 = user['profile']
                        user['profile'] = base64.b64encode(profile_image_base64).decode('utf-8')
                    else:
                        user['profile'] = None   

                return user_details

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/get_number_of_group_followers")
async def get_number_of_group_followers(
    groupid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor: 
                await cursor.execute(
                    "SELECT COUNT(*) AS count FROM group_users WHERE groupid = %s AND status =%s" ,
                    (groupid,1)
                )
                result = await cursor.fetchone()
                count = result['count'] if result else 0

        return JSONResponse(content={"count": count}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
@app.post("/check_group_join_accepted")
async def check_group_join_accepted(
    notificationid: str = Form(...),
    groupid: str = Form(...),
    myuserid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor: 
                await cursor.execute(
                    "SELECT status FROM group_users WHERE groupid = %s AND userid = %s",
                    (groupid, myuserid)
                )
                
                result = await cursor.fetchone()
                
                if result:
                    status = result['status']
                    if status == 0:
                        message = "no"
                    elif status == 1:
                        message = "yes"
                    else:
                        raise HTTPException(status_code=400, detail="Invalid status value")
                    
                    await cursor.execute(
                        "UPDATE notification SET seenstatus = %s WHERE notificationid = %s",
                        (1, notificationid)
                    )
                    await conn.commit()
                    
                    return JSONResponse(content={"message": message}, status_code=200)
                else:
                    raise HTTPException(status_code=404, detail="User not found in group")

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    






@app.post("/update_user_notification_seen_status")
async def update_user_notification_seen_status(
    userid: int = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE user
                    SET notificationstatus = 0
                    WHERE userid = %s
                """, (userid,))
                
                await conn.commit()

                return JSONResponse(content={"message": "seen"}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
            
            
            
            
            
            
            
              
    
    




@app.post("/ask_permission_from_admin_to_join_group")
async def ask_permission_from_admin_to_join_group(
    groupid: str = Form(...),
    groupownerid: str = Form(...),
    myuserid: str = Form(...),
):
    try:
        createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT status FROM group_users WHERE groupid = %s AND userid = %s",
                    (groupid, myuserid)
                )
                existing_user = await cursor.fetchone()
                
                if existing_user:
                    status = existing_user['status']
                    if status == 0:
                        return JSONResponse(content={"message": "requestsent"}, status_code=200)
                    elif status == 1:
                        return JSONResponse(content={"message": "requestaccepted"}, status_code=200)

                await cursor.execute(
                    "SELECT username, profileimage FROM user WHERE userid = %s",
                    (groupownerid,)
                )
                group_owner = await cursor.fetchone()
                
                if not group_owner:
                    raise HTTPException(status_code=404, detail="Group owner not found")
                
                group_owner_username = group_owner['username']
                group_owner_profileimage = group_owner.get('profileimage', None)
                
                await cursor.execute(
                    """
                    INSERT INTO notification (
                        postowneruserid, myuserid, username, notificationtype, commenttext,
                        date, userprofile, seenstatus, groupid
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        groupownerid, myuserid, group_owner_username, 'grouppermission', 'is asking permission to join your group',
                        createddate, group_owner_profileimage, 0, groupid
                    )
                )
                
                
                await cursor.execute("""
                    UPDATE user
                    SET notificationstatus = 1
                    WHERE userid = %s
                """, (groupownerid,))
                
                
                
                await cursor.execute(
                    "SELECT username, profileimage FROM user WHERE userid = %s",
                    (myuserid,)
                )
                user = await cursor.fetchone()
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                user_username = user['username']
                user_profileimage = user.get('profileimage', None)
                
                await cursor.execute(
                    """
                    INSERT INTO notification (
                        postowneruserid, myuserid, username, notificationtype, commenttext,
                        date, userprofile, seenstatus, groupid
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        myuserid, groupownerid, user_username, 'grouppermission', 'your request is sent to the group admin',
                        createddate, user_profileimage, 0, groupid
                    )
                )
                
                await cursor.execute("""
                    UPDATE user
                    SET notificationstatus = 1
                    WHERE userid = %s
                """, (myuserid,))
                
                
                await cursor.execute(
                    """
                    INSERT INTO group_users (groupid, userid, profileimage, username, usertype, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        groupid, myuserid, user_profileimage, user_username, 'user', 0
                    )
                )
                
                await conn.commit()
                
        return JSONResponse(content={"message": "Permission request sent successfully"}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    












@app.post("/log-in")
async def log_in(
    emailaddress: str = Form(...),
    password: str = Form(...),
):
    if not emailaddress or not password:
        return JSONResponse(content={"message": "Please enter credentials"}, status_code=400)

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = """
                SELECT emailaddress, password, userid, emailauth FROM user 
                WHERE emailaddress = %s AND password = %s
                """
                await cursor.execute(query, (emailaddress, password))
                user = await cursor.fetchone()

                if user:
                    if user['emailauth'] == 0:
                        return JSONResponse(content={"message": "Please confirm the email"}, status_code=200)
                    else:
                        
                        token_data = {"userid": user["userid"]}
                        token = create_access_token(token_data)

                        return JSONResponse(
                            content={"message": "Login successful", "userid": user["userid"], "token": token},
                            status_code=200
                        )
                        
                        
                        
                else:
                    return JSONResponse(content={"message": "No user found"}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




















@app.post("/log-in-with-google")
async def log_in_with_google(
    emailaddress: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = """
                SELECT emailaddress, userid, emailauth FROM user 
                WHERE emailaddress = %s
                """
                await cursor.execute(query, (emailaddress,))
                user = await cursor.fetchone()

                if user:
                    if user['emailauth'] == 0:
                        return JSONResponse(
                            content={"message": "Please confirm the email"},
                            status_code=200
                        )
                    else:
                        return JSONResponse(
                            content={
                                "message": "Email address already exists",
                                "userid": user["userid"]
                            },
                            status_code=200
                        )
                else:
                    return JSONResponse(
                        content={"message": "No user found"},
                        status_code=200
                    )

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

VIDEO_UPLOAD_DIR = "../ravoom/ravoom_social/src/assets/video_files"
AUDIO_UPLOAD_DIR = "../ravoom/ravoom_social/src/assets/audio_files"

Path(VIDEO_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(AUDIO_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def compress_video(input_video: BytesIO) -> BytesIO:
     
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input_file:
        temp_input_file.write(input_video.getvalue())
        temp_input_file_path = temp_input_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output_file:
        temp_output_file_path = temp_output_file.name

    try:
        with VideoFileClip(temp_input_file_path) as video: 
            video.write_videofile(temp_output_file_path, codec='libx264', bitrate='500k', audio_codec='aac', threads=4)
       

        with open(temp_output_file_path, "rb") as f:
            compressed_video = BytesIO(f.read())
        
        return compressed_video

    except Exception as e:
        print(f"Error compressing video: {e}")
        raise HTTPException(status_code=500, detail=f"Error compressing video: {str(e)}")

    finally:
         
        try:
            if os.path.exists(temp_input_file_path):
                os.remove(temp_input_file_path)
            if os.path.exists(temp_output_file_path):
                os.remove(temp_output_file_path)
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")


def generate_random_letter_string(length=30) -> str:
    if length <= 0:
        raise ValueError("Length must be positive")
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def generate_random_post_id(length=9) -> int:
    if length > 9:
        raise ValueError("Maximum length for post ID is 9 digits")
    min_value = 10**(length - 1)
    max_value = 10**length - 1
    return random.randint(min_value, max_value)


       
def string_to_int(s: str, length: int) -> int:
    letter_to_number = {chr(i): i - 64 for i in range(65, 91)}
    number = 0
    for char in s.upper():
        if char in letter_to_number:
            number = number * 26 + letter_to_number[char]
    max_value = 10**length - 1
    return number % max_value
          
def generate_combined_post_id(letter_string: str, length=9) -> int:
    letter_based_id = string_to_int(letter_string[:10], length)
    random_component = generate_random_post_id(length)
    combined_id = (letter_based_id * (10**(length - len(str(random_component))))) + random_component
    max_value = 10**length - 1
    return combined_id % max_value



@app.post("/add-post")
async def add_post(
    uid: int = Form(...),
    postdescription: str = Form(...),
    mediafile: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    try:
        if str(current_user) != str(uid):
            raise HTTPException(status_code=401, detail="Unauthorized access")

        media_data = await mediafile.read()
        media_data_stream = BytesIO(media_data)

        if mediafile.content_type.startswith('video'):
            posttype = 'video'
            media_data_stream = compress_video(media_data_stream)
        elif mediafile.content_type.startswith('audio'):
            posttype = 'audio'
        else:
            raise HTTPException(status_code=400, detail="Unsupported media type")

    except Exception as e:
        print(f"Error processing media file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing media file: {str(e)}")

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)
                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                insert_query = """
                INSERT INTO post (postid, userid, username, postdescription, posteddate, posttype, userprofile, post)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(
                    insert_query, 
                    (post_id, uid, username, postdescription, createddate, posttype, userprofile, media_data_stream.read())
                )

                await conn.commit()

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing media post in database")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error storing media post in database")

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)












 
@app.post("/add-post-group")
async def add_post_group(
    uid: int = Form(...),
    postdescription: str = Form(...),
    mediafile: UploadFile = File(...),
    groupid: str = Form(...),
    grouptype: str = Form(...),
    groupname: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    try:
        if str(current_user) != str(uid):
            raise HTTPException(status_code=401, detail="Unauthorized access")

        media_data = await mediafile.read()
        media_data_stream = BytesIO(media_data)

        if mediafile.content_type.startswith('video'):
            posttype = 'video'
            media_data_stream = compress_video(media_data_stream)
        elif mediafile.content_type.startswith('audio'):
            posttype = 'audio'
        else:
            raise HTTPException(status_code=400, detail="Unsupported media type")

        media_data_stream.seek(0)

    except Exception as e:
        print(f"Error processing media file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing media file: {str(e)}")

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)

                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                letter_string_group_post = generate_random_letter_string()
                post_id_group_post = generate_combined_post_id(letter_string_group_post)

                if grouptype == "public":
                    await cursor.execute("""
                        INSERT INTO post (postid, groupid, userid, username, postdescription, groupname, posteddate, posttype, userprofile, post, grouptype)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        post_id, groupid, uid, username, postdescription, groupname, createddate, posttype,
                        userprofile, media_data_stream.getvalue(), grouptype
                    ))

                await cursor.execute("""
                    INSERT INTO grouppost (postid, groupid, userid, username, postdescription, posteddate, posttype, userprofile, post)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    post_id_group_post, groupid, uid, username, postdescription, createddate, posttype,
                    userprofile, media_data_stream.getvalue()
                ))

                await conn.commit()

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing media post in database")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error storing media post in database")

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)







 



 




 
@app.post("/add-post-image")
async def add_post_image(
    uid: int = Form(...),
    imagePostdescription: str = Form(...),
    imagefile: list[UploadFile] = File(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    try:
        if str(current_user) != str(uid):
            raise HTTPException(status_code=401, detail="Unauthorized access")

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                print("Profile image data:", user.get('profileimage'))

                username = user['username']
                userprofile = user.get('profileimage', None)

                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                first_image_data = None
                if len(imagefile) > 0 and imagefile[0].content_type.startswith('image'):
                    first_image_data = await imagefile[0].read()

                await cursor.execute(
                    """
                    INSERT INTO post (postid, userid, username, postdescription, posteddate, posttype, post, userprofile)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (post_id, uid, username, imagePostdescription, createddate, 'image', first_image_data, userprofile)
                )

                await conn.commit()

                for index, file in enumerate(imagefile):
                    if file.content_type.startswith('image'):
                        if index == 0:
                            media_data = first_image_data
                        else:
                            media_data = await file.read()

                        await cursor.execute(
                            """
                            INSERT INTO image (postid, image)
                            VALUES (%s, %s)
                            """,
                            (post_id, media_data)
                        )

                await conn.commit()

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing image post in database")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)














@app.post("/add-post-image-group")
async def add_post_image_group(
    uid: int = Form(...),
    imagePostdescription: str = Form(...),
    imagefile: list[UploadFile] = File(...),
    groupid: str = Form(...),
    grouptype: str = Form(...),
    groupname: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    try:
        if str(current_user) != str(uid):
            raise HTTPException(status_code=401, detail="Unauthorized access")

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)

                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                letter_string_group_post = generate_random_letter_string()
                post_id_group_post = generate_combined_post_id(letter_string_group_post)

                image_data_list = []
                for index, file in enumerate(imagefile):
                    if file.content_type.startswith('image'):
                        media_data = await file.read()
                        if not media_data:
                            raise ValueError(f"Image data is empty for image index {index}")
                        image_data_list.append(media_data)

                first_image_data = image_data_list[0] if image_data_list else None

                if grouptype == "public":
                    await cursor.execute(
                        """
                        INSERT INTO post (postid, groupid, userid, username, postdescription, groupname, posteddate, posttype, post, userprofile, grouptype)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (post_id, groupid, uid, username, imagePostdescription, groupname, createddate, 'image', first_image_data, userprofile, grouptype)
                    )

                    for index, media_data in enumerate(image_data_list):
                        await cursor.execute(
                            """
                            INSERT INTO image (postid, image)
                            VALUES (%s, %s)
                            """,
                            (post_id, media_data)
                        )

                await cursor.execute(
                    """
                    INSERT INTO grouppost (postid, groupid, userid, username, postdescription, posteddate, posttype, post, userprofile)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (post_id_group_post, groupid, uid, username, imagePostdescription, createddate, 'image', first_image_data, userprofile)
                )

                for index, media_data in enumerate(image_data_list):
                    await cursor.execute(
                        """
                        INSERT INTO groupimage (postid, image)
                        VALUES (%s, %s)
                        """,
                        (post_id_group_post, media_data)
                    )
                    print(f"Inserted image {index + 1} into groupimage table")

                await conn.commit()
                print(f"Total images inserted: {len(image_data_list)}")

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing image post in database")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)













@app.post("/add-post-link")
async def add_post_link(
    uid: int = Form(...),
    imagePostdescription: str = Form(...),
    thelink: str = Form(...),
    linktitle: str = Form(...),
    linkimage: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user)
):
    if str(current_user) != str(uid):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)

                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                linkimageinsert = linkimage if linkimage is not None else ""

                await cursor.execute(
                    """
                    INSERT INTO post (
                        postid, userid, username, postdescription, posteddate, 
                        posttype, post, userprofile, filepath, textbody, thelink
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        post_id,
                        uid,
                        username,
                        imagePostdescription,
                        createddate,
                        'link',
                        linkimageinsert,  # 'post' field for storing preview image
                        userprofile,
                        linktitle,         # 'filepath' for storing link title
                        linkimageinsert,   # reuse in 'textbody' if needed
                        thelink
                    )
                )

                await conn.commit()

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing link post in database")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")

    return JSONResponse(content={"message": "Link post added successfully"}, status_code=201)















@app.post("/add-post-link-group")
async def add_post_link_group(
    uid: int = Form(...),
    imagePostdescription: str = Form(...),
    thelink: str = Form(...),
    linktitle: str = Form(...),
    linkimage: Optional[str] = Form(None),
    groupid: str = Form(...),
    groupname: str = Form(...),
    grouptype: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if str(current_user) != str(uid):
                    raise HTTPException(status_code=401, detail="Unauthorized access")

                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)

                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                letter_string_group_post = generate_random_letter_string()
                post_id_group_post = generate_combined_post_id(letter_string_group_post)

                linkimageinsert = linkimage if linkimage is not None else ""

                if grouptype == "public":
                    await cursor.execute(
                        """
                        INSERT INTO post (
                            postid, groupid, userid, username, postdescription, posteddate, posttype,
                            userprofile, filepath, textbody, thelink, groupname, grouptype
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (post_id, groupid, uid, username, imagePostdescription, createddate, 'link', userprofile,
                         linktitle, linkimageinsert, thelink, groupname, grouptype)
                    )
                    await conn.commit()

                await cursor.execute(
                    """
                    INSERT INTO grouppost (
                        postid, groupid, userid, username, postdescription, posteddate, posttype, userprofile,
                        filepath, textbody, thelink
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (post_id_group_post, groupid, uid, username, imagePostdescription, createddate, 'link',
                     userprofile, linktitle, linkimageinsert, thelink)
                )

                await conn.commit()

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing link post in database")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")
    
    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)














@app.post("/add-post-text")
async def add_text_post(
    userid: str = Form(...),
    selectedColor: str = Form(...),
    textPostbody: str = Form(...),
    textPostdescription: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if str(current_user) != userid:
                    raise HTTPException(status_code=401, detail="Unauthorized access")

                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (userid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)
                letter_string = generate_random_letter_string()
                post_id = generate_combined_post_id(letter_string)

                await cursor.execute(
                    """
                    INSERT INTO post (
                        postid, userid, username, postdescription, posteddate, posttype,
                        post, userprofile, filepath, textcolor, textbody
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (post_id, userid, username, textPostdescription, createddate, 'text', "",
                     userprofile, "", selectedColor, textPostbody)
                )
                
                await conn.commit()

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing text post in database")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)













@app.post("/add-post-text-group")
async def add_text_post_group(
    userid: str = Form(...),
    selectedColor: str = Form(...),
    textPostbody: str = Form(...),
    textPostdescription: str = Form(...),
    groupid: str = Form(...),
    groupname: str = Form(...),
    grouptype: str = Form(...),
    current_user: str = Depends(get_current_user),
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    if str(current_user) != userid:
        raise HTTPException(status_code=401, detail="Unauthorized access")

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (userid,))
                user = await cursor.fetchone()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user['username']
                userprofile = user.get('profileimage', None)
                letter_string = generate_random_letter_string()  
                post_id = generate_combined_post_id(letter_string)  
                
                letter_string_group_post = generate_random_letter_string()  
                post_id_group_post = generate_combined_post_id(letter_string_group_post)  

                if grouptype == "public":
                    await cursor.execute(
                        """
                        INSERT INTO post (
                            postid, groupid, userid, username, postdescription, posteddate, posttype, userprofile, textcolor, textbody, groupname, grouptype
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (post_id, groupid, userid, username, textPostdescription, createddate, 'text', userprofile, selectedColor, textPostbody, groupname, grouptype)
                    )

                await cursor.execute(
                    """
                    INSERT INTO grouppost (
                        postid, groupid, userid, username, postdescription, posteddate, posttype, userprofile, textcolor, textbody
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (post_id_group_post, groupid, userid, username, textPostdescription, createddate, 'text', userprofile, selectedColor, textPostbody)
                )
                
                await conn.commit()

            except aiomysql.MySQLError as err:
                print(f"Database error: {err}")
                raise HTTPException(status_code=500, detail="Error storing text post in database")
            except Exception as e:
                print(f"Error: {e}")
                raise HTTPException(status_code=500, detail="Error processing request")

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)



 
 










@app.get("/delete_post")
async def delete_post(
    postid: int = Query(...),
    userid: int = Query(...),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a post by its ID.

    Args:
    postid (int): The ID of the post to be deleted.

    Returns:
    JSONResponse: A JSON response indicating the result of the deletion.
    """
    try:
        if str(current_user) != str(userid):
            raise HTTPException(status_code=401, detail="Unauthorized access")

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                result = await cursor.execute("DELETE FROM post WHERE postid=%s", (postid,))
                
                if result == 0:
                    raise HTTPException(status_code=404, detail="Post not found")

                await conn.commit()

        return JSONResponse(content={"message": "Deleted"}, status_code=200)
    
    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error deleting post from database")
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
          

            
            
            
            
            
            
            
            
            
            
            
@app.get("/get_posts_feed_group")
async def get_posts_feed_group(
    limit: int = Query(5, ge=1),
    offset: int = Query(0, ge=0),
    groupid:str =Query(...),
    
    ):
    global pool
   
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute("""
                    SELECT * FROM grouppost WHERE groupid  =%s
                    ORDER BY posteddate DESC
                    LIMIT %s OFFSET %s
                """, (groupid,limit, offset))
                records = await cursor.fetchall()

                processed_records = []

                for record in records:
                    if record['posttype'] == 'image':
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid,
                                i.image,p.n_or_g
                            FROM grouppost p
                            LEFT JOIN groupimage i ON p.postid = i.postid
                            WHERE p.posttype = 'image' AND p.postid = %s
                            ORDER BY p.posteddate DESC
                        """, (record['postid'],))
                        image_records = await cursor.fetchall()

                        for image_record in image_records:
                            if image_record['image']:
                                image_record['image'] = base64.b64encode(image_record['image']).decode('utf-8')
                            if image_record['userprofile']:
                                image_record['userprofile'] = base64.b64encode(image_record['userprofile']).decode('utf-8')

                            processed_records.append(image_record)

                    elif record['posttype'] in ['video', 'audio', 'text', 'link','group']:
                        post_record = {
                            'postid': record['postid'],
                            'userid': record['userid'],
                            'username': record['username'],
                            'postdescription': record['postdescription'],
                            'posteddate': record['posteddate'],
                            'posttype': record['posttype'],
                            'post': base64.b64encode(record['post']).decode('utf-8') if record['post'] else None,
                            'userprofile': base64.b64encode(record['userprofile']).decode('utf-8') if record['userprofile'] else None,
                            'filepath': record['filepath'] if 'filepath' in record else None,
                            'textcolor': record['textcolor'] if 'textcolor' in record else None,
                            'textbody': record['textbody'] if 'textbody' in record else None,
                            'thelink': record['thelink'] if 'thelink' in record else None,
                            'groupid': record['groupid'] if 'groupid' in record else None,
                            'grouptype': record['grouptype'] if 'grouptype' in record else None,
                            'popularcount': record['popularcount'] if 'popularcount' in record else None,
                            'n_or_g': record['n_or_g'] if 'n_or_g' in record else None,
                        }

                        processed_records.append(post_record)

                return processed_records

            except aiomysql.Error as err:
                print(f"Error: {err}")
                raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
            
            
            
@app.get("/get_posts_feed")
async def get_posts_feed(
    limit: int = Query(5, ge=1), 
    offset: int = Query(0, ge=0),
    useridexported: str = Query(None)  
):
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                if useridexported:
                    await cursor.execute("""
                        SELECT blockeduserid FROM user_blocked WHERE userid = %s
                    """, (useridexported,))
                    blocked_users = await cursor.fetchall()
                    blocked_user_ids = [user['blockeduserid'] for user in blocked_users]

                    await cursor.execute("""
                        SELECT * FROM post
                        WHERE userid NOT IN (%s)
                        ORDER BY RAND()
                        LIMIT %s OFFSET %s
                    """, (', '.join(str(id) for id in blocked_user_ids), limit, offset))
                else:
                    await cursor.execute("""
                        SELECT * FROM post
                        ORDER BY RAND()
                        LIMIT %s OFFSET %s
                    """, (limit, offset))

                records = await cursor.fetchall()

                processed_records = []

                for record in records:
                    if record['posttype'] == 'image':
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid, p.n_or_g, p.groupname, p.groupid, p.grouptype,
                                i.image
                            FROM post p
                            LEFT JOIN image i ON p.postid = i.postid
                            WHERE p.posttype = 'image' AND p.postid = %s
                        """, (record['postid'],))
                        image_records = await cursor.fetchall()

                        for image_record in image_records:
                            if image_record['image']:
                                image_record['image'] = base64.b64encode(image_record['image']).decode('utf-8')
                            if image_record['userprofile']:
                                image_record['userprofile'] = base64.b64encode(image_record['userprofile']).decode('utf-8')

                            processed_records.append(image_record)

                    elif record['posttype'] in ['video', 'audio', 'text', 'link', 'group']:
                        post_record = {
                            'postid': record['postid'],
                            'userid': record['userid'],
                            'username': record['username'],
                            'postdescription': record['postdescription'],
                            'posteddate': record['posteddate'],
                            'posttype': record['posttype'],
                            'post': base64.b64encode(record['post']).decode('utf-8') if record['post'] else None,
                            'userprofile': base64.b64encode(record['userprofile']).decode('utf-8') if record['userprofile'] else None,
                            'filepath': record['filepath'] if 'filepath' in record else None,
                            'textcolor': record['textcolor'] if 'textcolor' in record else None,
                            'textbody': record['textbody'] if 'textbody' in record else None,
                            'thelink': record['thelink'] if 'thelink' in record else None,
                            'groupid': record['groupid'] if 'groupid' in record else None,
                            'grouptype': record['grouptype'] if 'grouptype' in record else None,
                            'n_or_g': record['n_or_g'] if 'n_or_g' in record else None,
                            'groupname': record['groupname'] if 'groupname' in record else None,
                        }

                        processed_records.append(post_record)

                return processed_records

            except aiomysql.Error as err:
                print(f"Error: {err}")
                raise HTTPException(status_code=500, detail="Internal Server Error")

            
            
            
            
            
            






@app.post("/blocking_user")
async def blocking_user(
    blockeduserid: str = Form(),
    curruntuserid: str = Form(),
):
    global pool

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(""" 
                    SELECT username, profileimage FROM user WHERE userid = %s 
                """, (blockeduserid,))
                user_details = await cursor.fetchone()

                if not user_details:
                    raise HTTPException(status_code=404, detail="User not found")

                await cursor.execute(""" 
                    SELECT * FROM user_blocked 
                    WHERE userid = %s AND blockeduserid = %s 
                """, (curruntuserid, blockeduserid))
                existing_block = await cursor.fetchone()

                if existing_block:
                    await cursor.execute(""" 
                        DELETE FROM user_blocked WHERE userid = %s AND blockeduserid = %s 
                    """, (curruntuserid, blockeduserid))
                    action = "unblocked"
                else:
                    await cursor.execute(""" 
                        INSERT INTO user_blocked (userid, blockeduserid, blockeddate, blockeduserprofile, username) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, (curruntuserid, blockeduserid, datetime.now(), user_details['profileimage'], user_details['username']))
                    action = "blocked"

                await conn.commit()

                return {"message": action}

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

            
            
            
            
            
            
            




    
    
    
    
  
  
  
  
  
  
  
  
  
  
  
  
  
  
@app.post("/get_posts_feed_option")
async def get_posts_feed_option(
    selectedOption: str = Form(),
    limit: int = Form(...),
    offset: int = Form(...)
    
    ):
 
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute("""
                    SELECT * FROM post WHERE posttype=%s
                    ORDER BY posteddate DESC LIMIT %s OFFSET %s
                """, (selectedOption,limit,offset))
                records = await cursor.fetchall()

                processed_records = []

                for record in records:
                    if record['posttype'] == 'image':
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid,p.n_or_g,p.groupname,p.groupid,p.grouptype,
                                i.image
                            FROM post p
                            LEFT JOIN image i ON p.postid = i.postid
                            WHERE p.posttype = 'image' AND p.postid = %s
                            ORDER BY p.posteddate DESC
                        """, (record['postid'],))
                        image_records = await cursor.fetchall()

                        for image_record in image_records:
                            if image_record['image']:
                                image_record['image'] = base64.b64encode(image_record['image']).decode('utf-8')
                            if image_record['userprofile']:
                                image_record['userprofile'] = base64.b64encode(image_record['userprofile']).decode('utf-8')

                            processed_records.append(image_record)

                    elif record['posttype'] in ['video', 'audio', 'text', 'link']:
                        post_record = {
                            'postid': record['postid'],
                            'userid': record['userid'],
                            'username': record['username'],
                            'postdescription': record['postdescription'],
                            'posteddate': record['posteddate'],
                            'posttype': record['posttype'],
                            'post': base64.b64encode(record['post']).decode('utf-8') if record['post'] else None,
                            'userprofile': base64.b64encode(record['userprofile']).decode('utf-8') if record['userprofile'] else None,
                            'filepath': record['filepath'] if 'filepath' in record else None,
                            'textcolor': record['textcolor'] if 'textcolor' in record else None,
                            'textbody': record['textbody'] if 'textbody' in record else None,
                            'thelink': record['thelink'] if 'thelink' in record else None,
                            'n_or_g': record['n_or_g'] if 'n_or_g' in record else None,
                        }

                        processed_records.append(post_record)

                return processed_records

            except aiomysql.Error as err:
                print(f"Error: {err}")
                raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
            
            
            
            
            
            
            
            
            
            
            
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
    
@app.post("/get_posts_feed_user")
async def get_posts_feed_user(
    userid: str = Form(...),
    limit: int = Form(...),
    offset: int = Form(...)
):
    cursor = None
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM post WHERE userid = %s ORDER BY posteddate DESC LIMIT %s OFFSET %s",
                    (userid, limit, offset)
                )
                records = await cursor.fetchall()

        processed_records = []

        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                for record in records:
                    if record['posttype'] == 'image':
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid, p.n_or_g,
                                   i.image
                            FROM post p
                            LEFT JOIN image i ON p.postid = i.postid
                            WHERE p.postid = %s
                            ORDER BY p.posteddate DESC
                        """, (record['postid'],))
                        image_records = await cursor.fetchall()

                        for image_record in image_records:
                            if image_record['image']:
                                image_record['image'] = base64.b64encode(image_record['image']).decode('utf-8')
                            if image_record['userprofile']:
                                image_record['userprofile'] = base64.b64encode(image_record['userprofile']).decode('utf-8')
                            processed_records.append(image_record)

                    elif record['posttype'] in ['video', 'audio', 'text', 'link', 'group']:
                        post_record = {
                            'postid': record['postid'],
                            'userid': record['userid'],
                            'username': record['username'],
                            'postdescription': record['postdescription'],
                            'posteddate': record['posteddate'],
                            'posttype': record['posttype'],
                            'post': base64.b64encode(record['post']).decode('utf-8') if isinstance(record['post'], bytes) else record['post'],
                            'userprofile': base64.b64encode(record['userprofile']).decode('utf-8') if isinstance(record['userprofile'], bytes) else record['userprofile'],
                            'filepath': record['filepath'] if 'filepath' in record else None,
                            'textcolor': record['textcolor'] if 'textcolor' in record else None,
                            'textbody': record['textbody'] if 'textbody' in record else None,
                            'thelink': record['thelink'] if 'thelink' in record else None,
                            'groupid': record['groupid'] if 'groupid' in record else None,
                            'grouptype': record['grouptype'] if 'grouptype' in record else None,
                            'n_or_g': record['n_or_g'] if 'n_or_g' in record else None,
                            'groupname': record['groupname'] if 'groupname' in record else None,
                        }
                        processed_records.append(post_record)

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        if cursor:
            await cursor.close()
            
            
            
            
            
            
            
            
            
            
            
            
            
            


@app.get("/get_fav_list")
async def get_posts_feed(
    userid: int = Query(...),
    limitfav: int = Query(5, ge=1),
    offsetfav: int = Query(0, ge=0)
):
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute("""
                    SELECT postid FROM favpost WHERE userid = %s ORDER BY saveeddate DESC  LIMIT %s OFFSET %s
                """, (userid, limitfav, offsetfav))
                fav_posts = await cursor.fetchall()

                post_ids = [post['postid'] for post in fav_posts]

                if not post_ids:
                    return []

                query = """
                    SELECT * FROM post WHERE postid IN %s
                """
                await cursor.execute(query, (post_ids,))
                records = await cursor.fetchall()

                processed_records = []

                for record in records:
                    if record['posttype'] == 'image':
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid, p.n_or_g, p.groupname, p.groupid, p.grouptype,
                                   i.image
                            FROM post p
                            LEFT JOIN image i ON p.postid = i.postid
                            WHERE p.posttype = 'image' AND p.postid = %s
                            ORDER BY p.posteddate DESC
                        """, (record['postid'],))
                        image_records = await cursor.fetchall()

                        for image_record in image_records:
                            if image_record['image']:
                                image_record['image'] = base64.b64encode(image_record['image']).decode('utf-8')
                            if image_record['userprofile']:
                                image_record['userprofile'] = base64.b64encode(image_record['userprofile']).decode('utf-8')

                            processed_records.append(image_record)

                    elif record['posttype'] in ['video', 'audio', 'text', 'link', 'group']:
                        post_record = {
                            'postid': record['postid'],
                            'userid': record['userid'],
                            'username': record['username'],
                            'postdescription': record['postdescription'],
                            'posteddate': record['posteddate'],
                            'posttype': record['posttype'],
                            'post': base64.b64encode(record['post']).decode('utf-8') if record['post'] else None,
                            'userprofile': base64.b64encode(record['userprofile']).decode('utf-8') if record['userprofile'] else None,
                            'filepath': record['filepath'] if 'filepath' in record else None,
                            'textcolor': record['textcolor'] if 'textcolor' in record else None,
                            'textbody': record['textbody'] if 'textbody' in record else None,
                            'thelink': record['thelink'] if 'thelink' in record else None,
                            'groupid': record['groupid'] if 'groupid' in record else None,
                            'grouptype': record['grouptype'] if 'grouptype' in record else None,
                            'n_or_g': record['n_or_g'] if 'n_or_g' in record else None,
                            'groupname': record['groupname'] if 'groupname' in record else None,
                        }

                        processed_records.append(post_record)

                return processed_records

            except aiomysql.Error as err:
                print(f"Error: {err}")
                raise HTTPException(status_code=500, detail="Internal Server Error")

            
            
        
        


            
            
            
            
            
            
            
            
            
            
                           
                    
            
@app.get("/get_followers_posts_feed")
async def get_followers_posts_feed(
    myuserid: str = Query(...),
    limit: int = Query(5, ge=1),
    offset: int = Query(0, ge=0)
):
    global pool
    
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                processed_records = []

                await cursor.execute("""
                    SELECT otheruserid, type, groupid FROM iamfollowing WHERE myuserid = %s
                """, (myuserid ))
                following_records = await cursor.fetchall()

                for record in following_records:
                    if record['type'] == 'user':
                        otheruserid = record['otheruserid']
                        
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid,
                                   p.grouptype, p.groupid, i.image, p.post, p.filepath, p.textcolor, p.textbody, p.thelink, p.n_or_g
                            FROM post p
                            LEFT JOIN image i ON p.postid = i.postid
                            WHERE p.userid = %s
                            ORDER BY  RAND() LIMIT %s OFFSET %s
                        """, (otheruserid, limit, offset))
                        
                        user_posts = await cursor.fetchall()

                        for post_record in user_posts:
                            detailed_post = {
                                'postid': post_record['postid'],
                                'userid': post_record['userid'],
                                'username': post_record['username'],
                                'postdescription': post_record['postdescription'],
                                'posteddate': post_record['posteddate'],
                                'posttype': post_record['posttype'],
                                'post': base64.b64encode(post_record['post']).decode('utf-8') if post_record['post'] else None,
                                'userprofile': base64.b64encode(post_record['userprofile']).decode('utf-8') if post_record['userprofile'] else None,
                                'filepath': post_record['filepath'] if 'filepath' in post_record else None,
                                'textcolor': post_record['textcolor'] if 'textcolor' in post_record else None,
                                'textbody': post_record['textbody'] if 'textbody' in post_record else None,
                                'thelink': post_record['thelink'] if 'thelink' in post_record else None,
                                'n_or_g': post_record['n_or_g'] if 'n_or_g' in post_record else None,
                                'grouptype': post_record['grouptype'] if 'grouptype' in post_record else None,
                                'groupid': post_record['groupid'] if 'groupid' in post_record else None,
                     
                            }

                            if post_record['posttype'] == 'image' and 'image' in post_record:
                                if post_record['image']:
                                    detailed_post['image'] = base64.b64encode(post_record['image']).decode('utf-8')
                                if post_record['userprofile']:
                                    detailed_post['userprofile'] = base64.b64encode(post_record['userprofile']).decode('utf-8')
                            elif post_record['posttype'] in ['video', 'audio', 'text', 'link']:
                                if 'post' in post_record and post_record['post']:
                                    detailed_post['post'] = base64.b64encode(post_record['post']).decode('utf-8')
                                if 'userprofile' in post_record and post_record['userprofile']:
                                    detailed_post['userprofile'] = base64.b64encode(post_record['userprofile']).decode('utf-8')

                            processed_records.append(detailed_post)

                    elif record['type'] == 'group':
                        groupid = record['groupid']
                        
                        await cursor.execute("""
                            SELECT gp.postid, gp.userid, gp.username, gp.postdescription, gp.posteddate, gp.posttype,
                                   gp.post, gp.filepath, gp.textcolor, gp.textbody, gp.thelink, gp.groupid, gp.userprofile,gp.n_or_g,
                                   gi.image
                            FROM grouppost gp
                            LEFT JOIN groupimage gi ON gp.postid = gi.postid
                            WHERE gp.groupid = %s
                            ORDER BY RAND()   LIMIT %s OFFSET %s
                        """, (groupid, limit, offset))
                        
                        group_posts = await cursor.fetchall()

                        for post_record in group_posts:
                            detailed_post = {
                                'postid': post_record['postid'],
                                'userid': post_record['userid'],
                                'username': post_record['username'],
                                'postdescription': post_record['postdescription'],
                                'posteddate': post_record['posteddate'],
                                'posttype': post_record['posttype'],
                                'post': base64.b64encode(post_record['post']).decode('utf-8') if post_record['post'] else None,
                                'userprofile': base64.b64encode(post_record['userprofile']).decode('utf-8') if post_record['userprofile'] else None,
                                'filepath': post_record['filepath'] if 'filepath' in post_record else None,
                                'textcolor': post_record['textcolor'] if 'textcolor' in post_record else None,
                                'textbody': post_record['textbody'] if 'textbody' in post_record else None,
                                'thelink': post_record['thelink'] if 'thelink' in post_record else None,
                                'n_or_g': post_record['n_or_g'] if 'n_or_g' in post_record else None,
                                'groupid': post_record['groupid'],
                            }

                            if post_record['posttype'] == 'image' and post_record.get('image'):
                                detailed_post['image'] = base64.b64encode(post_record['image']).decode('utf-8')

                            processed_records.append(detailed_post)

                return processed_records

            except aiomysql.Error as err:
                print(f"Error: {err}")
                raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        
            
 
@app.get("/get_comments_count")
async def get_comment_count(postid: int = Query(...)):
    global pool
    async with pool.acquire() as conn:   
        async with conn.cursor(aiomysql.DictCursor) as cursor:  
            await cursor.execute("SELECT COUNT(*) as comment_count FROM comment WHERE postid=%s", (postid,))
            record = await cursor.fetchone()
    
    if record:
        return JSONResponse(content={"comment_count": record['comment_count']}, status_code=200)
    else:
        return JSONResponse(content={"comment_count": 0}, status_code=200)

 
    
    
    



def serialize_blocked_user_data(record):
    """
    Serialize a single record (dictionary).
    """
    if not record:
        return None

    serialized_record = {}
    for key, value in record.items():
        if isinstance(value, datetime):
            serialized_record[key] = value.isoformat()
        elif isinstance(value, bytes):
            serialized_record[key] = base64.b64encode(value).decode('utf-8')
        else:
            serialized_record[key] = value

    return serialized_record

@app.post("/get_blocked_user_list")
async def get_blocked_user_list(userid: str = Form()):
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                await cursor.execute("""SELECT * FROM user_blocked WHERE userid = %s""", (userid,))

                user_details = await cursor.fetchall()
                
                serialized_users = [serialize_blocked_user_data(record) for record in user_details]

                return {"message": "Success", "blocked_users": serialized_users}

    except aiomysql.Error as err:
        print(f"Database Error: {err}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as general_err:
        print(f"Unexpected Error: {general_err}")
        raise HTTPException(status_code=500, detail="Unexpected Error")
    
    
    
        
    
    







def serialize_group_data(record):
    """
    Serialize a single record (dictionary).
    """
    if not record:
        return None

    serialized_record = {}
    for key, value in record.items():
        if isinstance(value, datetime):
            serialized_record[key] = value.isoformat()
        elif isinstance(value, bytes):  # Handling binary data for group image
            serialized_record[key] = base64.b64encode(value).decode('utf-8')
        else:
            serialized_record[key] = value

    return serialized_record


@app.post("/get_my_group_list")
async def get_my_group_list(userid: str = Form(...)):
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM groups WHERE groupownerid = %s", (userid,))
                user_details = await cursor.fetchall()

                serialized_groups = [serialize_group_data(record) for record in user_details]

                return {"message": "Success", "serialized_groups": serialized_groups}

    except aiomysql.Error as err:
        print(f"Database Error: {err}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as general_err:
        print(f"Unexpected Error: {general_err}")
        raise HTTPException(status_code=500, detail="Unexpected Error")
    
    
    




@app.post("/get_iamfollowing_group_list")
async def get_iamfollowing_group_list(userid: str = Form(...)):
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT groupid FROM iamfollowing WHERE myuserid = %s AND type = 'group'", (userid,))
                group_ids = await cursor.fetchall()   
                
                if not group_ids:
                    raise HTTPException(status_code=404, detail="No groups found that the user is following")
                
                group_ids = [group['groupid'] for group in group_ids]
                
                format_strings = ','.join(['%s'] * len(group_ids))   
                await cursor.execute(f"SELECT * FROM groups WHERE groupid IN ({format_strings})", tuple(group_ids))
                groups_details = await cursor.fetchall()
                
                serialized_groups = [serialize_group_data(record) for record in groups_details]

                return {"message": "Success", "serialized_my_follwoing_groups": serialized_groups}
    
    except aiomysql.Error as err:
        print(f"Database Error: {err}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as general_err:
        print(f"Unexpected Error: {general_err}")
        raise HTTPException(status_code=500, detail="Unexpected Error")

    
    
    
        
    
    
    
    
    

@app.post("/remove_blocked_user")
async def remove_blocked_user(
    blockeduserid: str = Form()):
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    DELETE FROM user_blocked WHERE blockeduserid = %s
                """, (blockeduserid,))

                await conn.commit()

                return {"message": "removed"}

    except aiomysql.Error as err:
        print(f"Database Error: {err}")
        raise HTTPException(status_code=500, detail="Database Error")
    except Exception as general_err:
        print(f"Unexpected Error: {general_err}")
        raise HTTPException(status_code=500, detail="Unexpected Error")
    
    
    
    
    
    
    
    
    
def serialize_record_iamfollowing(record):
    """
    Serialize a single record (dictionary).
    """
    if not record:
        return None
    
    serialized_record = {}
    for key in record:
        if isinstance(record[key], datetime):
            serialized_record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            serialized_record[key] = base64.b64encode(record[key]).decode('utf-8')
        else:
            serialized_record[key] = record[key]
    
    return serialized_record

@app.post("/get_iamfollowinguserlist")
async def get_iamfollowinguserlist(
    userid: int = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT * FROM iamfollowing
                    WHERE myuserid = %s AND type='user'
                """, (userid,))
                records = await cursor.fetchall()

                processed_records = [serialize_record_iamfollowing(record) for record in records]

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
       
    
    
    
    
    
 
 
 
 
 
 
 
 
 
 
 
 
 

@app.post("/get_populargroup")
async def get_populargroup():
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT * FROM groupmembercount 
                    ORDER BY members DESC LIMIT 20
                """)
                records = await cursor.fetchall()

                processed_records = [serialize_record_iamfollowing(record) for record in records]

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
def serialize_record_user(record):
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/get_userlist")
async def get_userlist(
    currentuserid: int = Form(...)
):
     
    try:
       
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT DISTINCT userid 
                    FROM post_like 
                    WHERE currentuserid = %s AND userid !=%s LIMIT 20
                """, (currentuserid,currentuserid))
                
                user_ids = await cursor.fetchall()

                processed_records = []
                for result in user_ids:
                    otheruserid = result['userid']
                    await cursor.execute("SELECT * FROM user WHERE userid=%s", (otheruserid,))
                    record = await cursor.fetchone()

                    if record:
                        processed_record = serialize_record_user(record)
                        processed_records.append(processed_record)

        return JSONResponse(content=processed_records, status_code=200)

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
       
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
       
  
            
            
     







def serialize_record(record):
    """
    Serialize a single record (dictionary) or a list of records.
    Returns None if the record is None or empty.
    """
    if not record:
        return None
    
    if isinstance(record, dict):
        serialized_record = {}
        for key in record:
            if isinstance(record[key], datetime):
                serialized_record[key] = record[key].isoformat()
            elif isinstance(record[key], bytes):
                serialized_record[key] = base64.b64encode(record[key]).decode('utf-8')
            else:
                serialized_record[key] = record[key]
        return serialized_record
    
    elif isinstance(record, list):
        return [serialize_record(rec) for rec in record if rec]

    return None

@app.post("/get_notifications")
async def get_notifications(
    userid: int = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT n.notificationid, n.postid, n.postowneruserid,n.commenttext,n.groupid,n.groupname,n.replaytext, n.myuserid, n.username, n.notificationtype, n.date, u.profileimage, n.seenstatus,n.n_or_g
                    FROM notification n
                    JOIN user u ON n.myuserid = u.userid
                    WHERE n.postowneruserid = %s
                    ORDER BY n.date DESC LIMIT 30
                """, (userid,))
                records = await cursor.fetchall()

                processed_records = []

                for record in records:
                    processed_record = serialize_record(record)
                    processed_records.append(processed_record)

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
def serialize_record_iamfollowed(record):
    """
    Serialize a single record (dictionary).
    """
    if not record:
        return None
    
    serialized_record = {}
    for key in record:
        if isinstance(record[key], datetime):
            serialized_record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            serialized_record[key] = base64.b64encode(record[key]).decode('utf-8')
        else:
            serialized_record[key] = record[key]
    
    return serialized_record

@app.post("/get_iamfolloweduserlist")
async def get_iamfolloweduserlist(
    userid: int = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT * FROM iamfollowed
                    WHERE myuserid = %s
                """, (userid,))
                records = await cursor.fetchall()

                processed_records = [serialize_record_iamfollowed(record) for record in records]

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    



          







def serialize_record_liked_members_details(record):
    """
    Serialize a single record (dictionary).
    """
    if not record:
        return None
    
    serialized_record = {}
    for key in record:
        if isinstance(record[key], datetime):
            serialized_record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            serialized_record[key] = base64.b64encode(record[key]).decode('utf-8')
        else:
            serialized_record[key] = record[key]
    
    return serialized_record

@app.post("/get_liked_members")
async def get_liked_members(
    postid: str = Form(...),
    limit: int = Form(...),
    offset: int = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT pl.currentuserid, u.username, u.profileimage
                    FROM post_like pl
                    INNER JOIN user u ON pl.currentuserid = u.userid
                    WHERE pl.postid = %s LIMIT %s OFFSET %s
                """, (postid, limit, offset))
                records = await cursor.fetchall()

                processed_records = [serialize_record_liked_members_details(record) for record in records]

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    



@app.post("/get_liked_members_group")
async def get_liked_members_group(
    postid: str = Form(...),
    limit: int = Form(...),
    offset: int = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT pl.currentuserid, u.username, u.profileimage
                    FROM group_post_like pl
                    INNER JOIN user u ON pl.currentuserid = u.userid
                    WHERE pl.postid = %s LIMIT %s OFFSET %s
                """, (postid, limit, offset))
                records = await cursor.fetchall()

                processed_records = [serialize_record_liked_members_details(record) for record in records]

        return processed_records

    except aiomysql.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    





            
            
@app.post("/add_post_like")
async def add_post_like(
    postid: int = Form(...),
    userid: int = Form(...),
    currentuserid: int = Form(...),
    username: str = Form(...),
    profileimage: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:

                check_query = "SELECT * FROM post_like WHERE postid = %s AND currentuserid = %s"
                await cursor.execute(check_query, (postid, currentuserid))
                existing_like = await cursor.fetchone()

                if existing_like:
                    delete_query = "DELETE FROM post_like WHERE postid = %s AND currentuserid = %s"
                    await cursor.execute(delete_query, (postid, currentuserid))
                    await conn.commit()
                    return JSONResponse(content={"message": "yes"}, status_code=200)
                
                insert_query = """
                INSERT INTO post_like (postid, userid, currentuserid, username, profileimage)
                VALUES (%s, %s, %s, %s, %s)
                """
                await cursor.execute(insert_query, (postid, userid, currentuserid, username, profileimage))
                await conn.commit()
                
                return JSONResponse(content={"message": "no"}, status_code=201)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected Error")

















@app.post("/add_post_like_group")
async def add_post_like_group(
    postid: int = Form(...),
    userid: int = Form(...),
    currentuserid: int = Form(...),
    username: str = Form(...),
    profileimage: str = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:

                check_query = "SELECT * FROM group_post_like WHERE postid = %s AND currentuserid = %s"
                await cursor.execute(check_query, (postid, currentuserid))
                existing_like = await cursor.fetchone()

                if existing_like:
                    delete_query = "DELETE FROM group_post_like WHERE postid = %s AND currentuserid = %s"
                    await cursor.execute(delete_query, (postid, currentuserid))
                    await conn.commit()
                    return JSONResponse(content={"message": "yes"}, status_code=200)
                
                insert_query = """
                INSERT INTO group_post_like (postid, userid, currentuserid, username, profileimage)
                VALUES (%s, %s, %s, %s, %s)
                """
                await cursor.execute(insert_query, (postid, userid, currentuserid, username, profileimage))
                await conn.commit()

                return JSONResponse(content={"message": "no"}, status_code=201)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected Error")







 
 
 
 
@app.post("/save_fav_post")
async def save_fav_post(
    postid: int = Form(...),
    userid: int = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT * FROM favpost WHERE postid = %s AND userid = %s"
                await cursor.execute(check_query, (postid, userid))
                existing_like = await cursor.fetchone()

                if existing_like:
                    delete_query = "DELETE FROM favpost WHERE postid = %s AND userid = %s"
                    await cursor.execute(delete_query, (postid, userid))
                    await conn.commit()
                    return JSONResponse(content={"message": "removed"}, status_code=200)

                insert_query = """
                INSERT INTO favpost (postid, userid, saveeddate)
                VALUES (%s, %s, NOW())
                """
                await cursor.execute(insert_query, (postid, userid))
                await conn.commit()

                return JSONResponse(content={"message": "saved"}, status_code=201)

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error interacting with the database")
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")















@app.post("/is_added_to_fav")
async def is_added_to_fav(
    postid: int = Form(...),
    userid: int = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                check_query = "SELECT * FROM favpost WHERE postid = %s AND userid = %s"
                await cursor.execute(check_query, (postid, userid))
                existing_like = await cursor.fetchone()

                if existing_like:
                    return JSONResponse(content={"message": "exists"}, status_code=200)
                else:
                    return JSONResponse(content={"message": "not_found"}, status_code=200)

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error interacting with the database")
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    
    
    
    
    
    



    
    
@app.post("/send-notification")
async def send_notification(
    postid: int = Form(...),
    userid: int = Form(...),
    currentuserid: int = Form(...),
    username: str = Form(...),
    commenttext: str = Form(...),
    notificationtype: str = Form(...),
    profileimage: str = Form(...),
    replytext: str = Form(...),
):
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
 

    try:
        async with pool.acquire() as conn:   
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT username, profileimage FROM user WHERE userid = %s
                """, (currentuserid,))
                user_details = await cursor.fetchone()

                if not user_details:
                    raise HTTPException(status_code=404, detail="User not found")

                username = user_details['username']
                profileimagecurruntuser = user_details['profileimage']

                if notificationtype == 'like':
                    await cursor.execute("""
                        SELECT COUNT(*) as count FROM notification
                        WHERE postid = %s AND myuserid  = %s  AND notificationtype = %s
                    """, (postid, currentuserid, 'like'))
                    
                    result = await cursor.fetchone()

                    if result['count'] > 0:
                        await cursor.execute("""
                            DELETE FROM notification
                            WHERE postid = %s AND myuserid  = %s  AND notificationtype = %s
                        """, (postid, currentuserid, 'like'))
                        await conn.commit() 

                        return JSONResponse(content={"message": "Existing like notification dropped"}, status_code=200)
                    else:
                        await cursor.execute("""
                            INSERT INTO notification (postid, postowneruserid, myuserid, username, notificationtype, commenttext, replaytext, date, userprofile, seenstatus)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (postid, userid, currentuserid, username, notificationtype, "", "", createddate, profileimagecurruntuser, 0))

                elif notificationtype == "comment":
                    await cursor.execute("""
                        INSERT INTO notification (postid, postowneruserid, myuserid, username, notificationtype, commenttext, replaytext, date, userprofile, seenstatus)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (postid, userid, currentuserid, username, notificationtype, commenttext, "", createddate, profileimagecurruntuser, 0))
                    
                elif notificationtype == "replaycomment":
                    await cursor.execute("""
                        INSERT INTO notification (postid, postowneruserid, myuserid, username, notificationtype, commenttext, replaytext, date, userprofile, seenstatus)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (postid, userid, currentuserid, username, notificationtype, commenttext, replytext, createddate, profileimagecurruntuser, 0))
                    
                await cursor.execute("""
                    UPDATE user
                    SET notificationstatus = 1
                    WHERE userid = %s
                """, (userid,))

                await conn.commit()   
                return JSONResponse(content={"message": "Notification added successfully"}, status_code=201)
                    

    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Database Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
   
    
    
 


@app.get("/get_like_count")
async def get_like_count(postid: int = Query(...)):
    global pool
    async with pool.acquire() as conn:   
        async with conn.cursor(aiomysql.DictCursor) as cursor: 
            await cursor.execute("SELECT COUNT(*) as like_count FROM post_like WHERE postid=%s", (postid,))
            record = await cursor.fetchone()
    
    if record:
        return JSONResponse(content={"like_count": record['like_count']}, status_code=200)
    else:
        return JSONResponse(content={"like_count": 0}, status_code=200)
    
    
    
    
    
    
    
    
    
    
@app.get("/get_like_count_group")
async def get_like_count_group(postid: int = Query(...)):
    global pool
    async with pool.acquire() as conn:   
        async with conn.cursor(aiomysql.DictCursor) as cursor: 
            await cursor.execute("SELECT COUNT(*) as like_count FROM group_post_like WHERE postid=%s", (postid,))
            record = await cursor.fetchone()
    
    if record:
        return JSONResponse(content={"like_count": record['like_count']}, status_code=200)
    else:
        return JSONResponse(content={"like_count": 0}, status_code=200)
    
    
    
    
    
    
    
    
    
  
  
  
@app.get("/check_curruntuser_liked_or_not_group")
async def check_curruntuser_liked_or_not_group(
    postid: int = Query(...),
    userid: int = Query(...)
):
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT currentuserid, userid FROM group_post_like WHERE postid=%s AND currentuserid=%s", 
                (postid, userid)
            )
            record = await cursor.fetchone()

    if record:
        return JSONResponse(content={"message": "yes"}, status_code=200)
    else:
        return JSONResponse(content={"message": "no"}, status_code=200)
    
    
      
    
    
    





@app.get("/check_curruntuser_liked_or_not")
async def check_curruntuser_liked_or_not(
    postid: int = Query(...),
    userid: int = Query(...)
):
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT currentuserid, userid FROM post_like WHERE postid=%s AND currentuserid=%s", 
                (postid, userid)
            )
            record = await cursor.fetchone()

    if record:
        return JSONResponse(content={"message": "yes"}, status_code=200)
    else:
        return JSONResponse(content={"message": "no"}, status_code=200)
    
    
    
    
    
    
  
  
  
  




@app.get("/check_curruntuser_liked_video_or_not")
async def check_curruntuser_liked_video_or_not(
    postid: int = Query(...),
    userid: int = Query(...)
):
    global pool
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT currentuserid, userid FROM post_like WHERE postid=%s AND currentuserid=%s", 
                (postid, userid)
            )
            record = await cursor.fetchone()

    if record:
        return JSONResponse(content={"message": "yes"}, status_code=200)
    else:
        return JSONResponse(content={"message": "no"}, status_code=200)
    
    
    
    
    
    
    
    
    
    
    
      
    
@app.get("/get_replay_count")
async def get_replay_count(commentid: int = Query(...)):
    global pool
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT COUNT(*) as replay_count FROM commentreply WHERE commentid = %s", (commentid,))
                record = await cursor.fetchone()

        if record:
            return JSONResponse(content={"replays_count": record['replay_count']}, status_code=200)
        else:
            return JSONResponse(content={"replays_count": 0}, status_code=200)

    except Exception as e:
        print(f"Error fetching replay count: {e}")
        return JSONResponse(content={"message": "Error fetching replay count"}, status_code=500)
    
    
    
    
    
    
    
def serialize_record(record):
    """
    Serialize the database record to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.get("/get-popular-posts-from-like-count")
async def get_popular_posts_from_like_count():
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT postid, COUNT(*) as like_count 
                    FROM post_like 
                    GROUP BY postid 
                    ORDER BY like_count DESC  LIMIT 10
                """)
                like_counts = await cursor.fetchall()

                if like_counts:
                    post_ids = [record['postid'] for record in like_counts]
                    placeholders = ', '.join(['%s'] * len(post_ids))

                    await cursor.execute(f"SELECT * FROM post WHERE postid IN ({placeholders})", tuple(post_ids))
                    posts = await cursor.fetchall()

                    serialized_posts = [serialize_record(post) for post in posts]

                    return JSONResponse(content={"posts": serialized_posts, "like_counts": like_counts}, status_code=200)
                else:
                    return JSONResponse(content={"message": "No popular posts found"}, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
@app.get("/following-status")
async def following_status(
    postownerid: str = Query(...),
    userid: str = Query(...),
):
    global pool
    async with pool.acquire() as conn:   
        async with conn.cursor(aiomysql.DictCursor) as cursor:  
            await cursor.execute(
                "SELECT myuserid, otheruserid FROM iamfollowed WHERE myuserid=%s AND otheruserid=%s", 
                (postownerid, userid)  
            )
            record = await cursor.fetchone()  

    if record:
        return JSONResponse(content={"exists": True}, status_code=200)
    else:
        return JSONResponse(content={"exists": False}, status_code=200)
        
        
        
    
    
    
    
    
@app.post("/update-user-details")
async def update_user_details(
    userid: int = Form(...),
    username: str = Form(...),
    emailaddress: str = Form(...),
    phonenumber: str = Form(...),
):
    global pool
    try:
        async with pool.acquire() as conn:  
            async with conn.cursor(aiomysql.DictCursor) as cursor:  
                await cursor.execute("SELECT profileimage FROM user WHERE userid = %s", (userid,))
                user_record = await cursor.fetchone()

                if not user_record:
                    raise HTTPException(status_code=404, detail=f"User with userid {userid} not found")
                
                user_profileimage = user_record['profileimage']

                await cursor.execute(
                    "UPDATE user SET username = %s, emailaddress = %s, phonenumber = %s, profileimage = %s WHERE userid = %s",
                    (username, emailaddress, phonenumber, user_profileimage, userid)
                )
                await conn.commit()

                await cursor.execute(
                    "UPDATE post SET username = %s WHERE userid = %s",
                    (username, userid)
                )
                await conn.commit()

                affected_rows = cursor.rowcount

                if affected_rows > 0:
                    return JSONResponse(content={"message": "User details updated successfully"}, status_code=200)
                else:
                    raise HTTPException(status_code=404, detail=f"User with userid {userid} not found")

    except Exception as e:
        return JSONResponse(content={"message": f"Internal Server Error: {str(e)}"}, status_code=500)


 
    
    
    
    
    
    
    






@app.post("/update_notification_status")
async def update_notification_status(
    userid: int = Form(...),
):
    try:
        async with pool.acquire() as conn:  
            async with conn.cursor(aiomysql.DictCursor) as cursor:  
                await cursor.execute(
                    "UPDATE user SET notificationstatus = %s WHERE userid = %s",
                    (0, userid)
                )
                await conn.commit()

                affected_rows = cursor.rowcount

                if affected_rows > 0:
                    return JSONResponse(content={"message": "User details updated successfully"}, status_code=200)
                else:
                    raise HTTPException(status_code=404, detail=f"User with userid {userid} not found")

    except Exception as e:
        return JSONResponse(content={"message": f"Internal Server Error: {str(e)}"}, status_code=500)
    
    
    
    
    
    
    
    
    
    
        
    
@app.post("/update-notification-clicked")
async def update_notification_clicked(notificationid: str = Form(...)):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "UPDATE notification SET seenstatus = %s WHERE notificationid = %s",
                    (1, notificationid)
                )
                await conn.commit()   

        return JSONResponse(content={"message": "Notification status updated successfully"}, status_code=200)

    except aiomysql.Error as e:
        print(f"Database Error: {e}")
        return JSONResponse(content={"message": f"Database Error: {str(e)}"}, status_code=500)

    except Exception as e:
        print(f"Internal Server Error: {e}")
        return JSONResponse(content={"message": f"Internal Server Error: {str(e)}"}, status_code=500)
    
    
    
    
    
ACCESS_TOKEN = "968961804690906|RSgys8QNZ-Nh-9AuMLO8wF3wB3E"

@app.post("/get-preview")
async def get_link_preview(url: str = Form(...)):
    try:
        if 'facebook.com' in url or 'instagram.com' in url:
            preview_data = await fetch_facebook_preview(url)
        else:
            preview_data = await fetch_general_preview(url)
        return JSONResponse(content=preview_data)
    except HTTPException as e:
        return JSONResponse(content={"message": e.detail}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"message": f"Internal Server Error: {str(e)}"}, status_code=500)


async def fetch_facebook_preview(url: str):
    try:
        graph_api_url = f'https://graph.facebook.com/v11.0/?id={url}&access_token={ACCESS_TOKEN}'
        async with httpx.AsyncClient() as client:
            response = await client.get(graph_api_url, timeout=10)
            response.raise_for_status()
        preview_data = response.json()

        return {
            'title': preview_data.get('title', url),
            'description': preview_data.get('description', ''),
            'img': preview_data.get('image'),
            'domain': urlparse(url).netloc,
            'site_name': preview_data.get('site_name', urlparse(url).netloc),
            'facebook_app_id': preview_data.get('fb_app_id', ''),
            'url': url
        }
    except Exception:
        return await fetch_general_preview(url)


async def fetch_general_preview(url: str):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10, follow_redirects=True)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'}) or soup.title
        description = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        image = soup.find('meta', property='og:image')
        site_name = soup.find('meta', property='og:site_name')

        title = title.get('content') if title and hasattr(title, 'get') else title.string if title else url
        description = description.get('content') if description else None
        image_url = image.get('content') if image else None
        site_name = site_name.get('content') if site_name else urlparse(url).netloc

        if not image_url:
            first_img = soup.find('img')
            if first_img and first_img.get('src'):
                image_url = first_img['src']
                if image_url.startswith('/'):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    image_url = base_url + image_url

        return {
            'title': title,
            'description': description,
            'img': image_url,
            'domain': urlparse(url).netloc,
            'site_name': site_name,
            'url': url
        }

    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Error while fetching URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch the URL: {str(e)}")

    
 
 
 
 
 
 
 

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def serialize_record(record):
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/get_post")
async def get_post(
    postid: int = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM post WHERE postid=%s", (postid,))
                record = await cursor.fetchone()

                if record:
                    record = serialize_record(record)
                    return JSONResponse(content=record, status_code=200)
                else:
                    return JSONResponse(content={"message": "Post not found"}, status_code=404)
    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error interacting with the database")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    
    
    
    
    
    
    
    
@app.post("/get_post_group")
async def get_post_group(
    postid: int = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM grouppost WHERE postid=%s", (postid,))
                record = await cursor.fetchone()

                if record:
                    record = serialize_record_group(record)
                    return JSONResponse(content=record, status_code=200)
                else:
                    return JSONResponse(content={"message": "Post not found"}, status_code=404)
    except aiomysql.MySQLError as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error interacting with the database")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")







def serialize_record_image(record):
    """
    Serialize a single record or a list of records.
    """
    if isinstance(record, dict):
        for key in record:
            if isinstance(record[key], datetime):
                record[key] = record[key].isoformat()
            elif isinstance(record[key], bytes):
                record[key] = base64.b64encode(record[key]).decode('utf-8')
    elif isinstance(record, list):
        for rec in record:
            serialize_record_image(rec)
    return record

@app.post("/get_images")
async def get_images(postid: int = Form(...)):
    print(f"postid: {postid}")

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM image WHERE postid=%s", (postid,))
            records = await cursor.fetchall()  

    if records:
        serialized_records = serialize_record_image(records)
        return JSONResponse(content=serialized_records, status_code=200)
    else:
        return JSONResponse(content={"message": "Images not found for the post"}, status_code=404)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
def serialize_record_image_group(record):
    """
    Serialize a single record or a list of records.
    """
    if isinstance(record, dict):
        for key in record:
            if isinstance(record[key], datetime):
                record[key] = record[key].isoformat()
            elif isinstance(record[key], bytes):
                record[key] = base64.b64encode(record[key]).decode('utf-8')
    elif isinstance(record, list):
        for rec in record:
            serialize_record_image(rec)
    return record

@app.post("/get_images_group")
async def get_images_group(postid: int = Form(...)):
     

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM groupimage WHERE postid=%s", (postid,))
            records = await cursor.fetchall()  

    if records:
        serialized_records = serialize_record_image_group(records)
        return JSONResponse(content=serialized_records, status_code=200)
    else:
        return JSONResponse(content={"message": "Images not found for the post"}, status_code=404)
    
    
    
    
    
    
    
@app.post("/add_comment")
async def add_comment(
    postid: int = Form(...),
    userid: int = Form(...),
    username: str = Form(...),
    groupornormalpost: str = Form(...),
    userprofile: str = Form(...),
    commenttext: str = Form(None),   
    selectedImage: UploadFile = File(None)   
):
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
         
        image_data = None
        if selectedImage:
            image_data = await selectedImage.read()

        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                insert_query = """
                INSERT INTO comment (postid, userid, username, text, commenteddate, userprofile, n_or_g, commentimage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                await cursor.execute(insert_query, (
                    postid, 
                    userid, 
                    username, 
                    commenttext if commenttext else "",  
                    createddate, 
                    userprofile, 
                    groupornormalpost,
                    image_data   
                ))
                await conn.commit()

        return JSONResponse(content={"message": "Comment added successfully"}, status_code=201)

    except Exception as e:
        print(f"Error inserting comment: {e}")
        return JSONResponse(content={"message": "Error adding comment"}, status_code=500)

    
    
    
    
    
    
    
    
    
    
@app.post("/add_comment_group")
async def add_comment_group(
    postid: int = Form(...),
    userid: int = Form(...),
    username: str = Form(...),
    groupornormalpost: str = Form(...),
    userprofile: str = Form(...),
    commenttext: str = Form(None),   
    selectedImage: UploadFile = File(None)   
):
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
         
        image_data = None
        if selectedImage:
            image_data = await selectedImage.read()

        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                insert_query = """
                INSERT INTO groupcomment (postid, userid, username, text, commenteddate, userprofile, n_or_g, commentimage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                await cursor.execute(insert_query, (
                    postid, 
                    userid, 
                    username, 
                    commenttext if commenttext else "",  
                    createddate, 
                    userprofile, 
                    groupornormalpost,
                    image_data   
                ))
                await conn.commit()

        return JSONResponse(content={"message": "Comment added successfully"}, status_code=201)

    except Exception as e:
        print(f"Error inserting comment: {e}")
        return JSONResponse(content={"message": "Error adding comment"}, status_code=500)


    
 
    
    
    
    
    
@app.post("/add_replay_comment")
async def add_replay_comment(
    postid: int = Form(...),
    commentid: int = Form(...),
    userid: int = Form(...),
    username: str = Form(...),
    groupornormalpost: str = Form(...),
    userprofile: str = File(...),
    replytext: str = Form(...)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                
                
                await cursor.execute("SELECT profileimage FROM user WHERE userid = %s", (userid,))
                user_record = await cursor.fetchone()

                if not user_record:
                    raise HTTPException(status_code=404, detail=f"User with userid {userid} not found")
                
                user_profileimage = user_record['profileimage']
                
                insert_query = """
                INSERT INTO commentreply (commentid, postid, userid, username, text, replayeddate, userprofile,n_or_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s,%s)
                """
                await cursor.execute(insert_query, (commentid, postid, userid, username, replytext, createddate, user_profileimage,groupornormalpost))
                await conn.commit()
                
                
                
        cursor.execute(insert_query, (commentid,postid, userid, username, replytext,createddate,userprofile))
        conn.commit()
        cursor.close()
        return JSONResponse(content={"message": "replay Comment added successfully"}, status_code=201)
    except mysql.connector.Error as e:
        print(f"Error inserting comment: {e}")
        return JSONResponse(content={"message": "Error adding replay comment"}, status_code=500)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/add_replay_comment_group")
async def add_replay_comment_group(
    postid: int = Form(...),
    commentid: int = Form(...),
    userid: int = Form(...),
    username: str = Form(...),
    groupornormalpost: str = Form(...),
    userprofile: str = File(...),
    replytext: str = Form(...)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                insert_query = """
                INSERT INTO groupcommentreplay (commentid, postid, userid, username, text, replayeddate, userprofile,n_or_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s,%s)
                """
                await cursor.execute(insert_query, (commentid, postid, userid, username, replytext, createddate, userprofile,groupornormalpost))
                await conn.commit()
                
                
                
        cursor.execute(insert_query, (commentid,postid, userid, username, replytext,createddate,userprofile))
        conn.commit()
        cursor.close()
        return JSONResponse(content={"message": "replay Comment added successfully"}, status_code=201)
    except mysql.connector.Error as e:
        print(f"Error inserting comment: {e}")
        return JSONResponse(content={"message": "Error adding replay comment"}, status_code=500)
    
    
  

    
    
    
    
    
 
 

def serialize_record_comments(records):
    for record in records:
        for key in record:
            if isinstance(record[key], datetime):
                record[key] = record[key].isoformat()  # Convert datetime to ISO string
            elif isinstance(record[key], bytes):
                record[key] = base64.b64encode(record[key]).decode('utf-8')  # Base64 encode binary data
    return records








@app.get("/get_comments")
async def get_comments(
    postid: str = Query(...),
    commentslimit: int = Query(10, ge=1),
    last_comment_id: int = Query(None)   
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if last_comment_id:
                    await cursor.execute(
                        """
                        SELECT c.commentid, c.postid,c.commentimage,c.n_or_g, c.userid, u.username, c.text, c.commenteddate, u.profileimage
                        FROM comment c
                        INNER JOIN user u ON c.userid = u.userid
                        WHERE c.postid = %s AND c.commentid < %s
                        ORDER BY c.commenteddate DESC
                        LIMIT %s
                        """,
                        (postid, last_comment_id, commentslimit)
                    )
                else:
                    await cursor.execute(
                        """
                        SELECT c.commentid, c.postid,c.commentimage,c.n_or_g, c.userid, u.username, c.text, c.commenteddate, u.profileimage
                        FROM comment c
                        INNER JOIN user u ON c.userid = u.userid
                        WHERE c.postid = %s
                        ORDER BY c.commenteddate DESC
                        LIMIT %s
                        """,
                        (postid, commentslimit)
                    )

                records = await cursor.fetchall()

                if not records:
                    return JSONResponse(content={"comments": []}, status_code=200)

                serialized_records = serialize_record_comments(records)
                return JSONResponse(content={"comments": serialized_records}, status_code=200)

    except aiomysql.MySQLError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




    
    
    
    
    
    
    
    
    
@app.get("/get_comments_group")
async def get_comments_group(
    postid: str = Query(...),
    commentslimit: int = Query(10, ge=1),
    last_comment_id: int = Query(None)   
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if last_comment_id:
                    await cursor.execute(
                        """
                        SELECT c.commentid, c.postid,c.commentimage,c.n_or_g, c.userid, u.username, c.text, c.commenteddate, u.profileimage
                        FROM groupcomment c
                        INNER JOIN user u ON c.userid = u.userid
                        WHERE c.postid = %s AND c.commentid < %s
                        ORDER BY c.commenteddate DESC
                        LIMIT %s
                        """,
                        (postid, last_comment_id, commentslimit)
                    )
                else:
                    await cursor.execute(
                        """
                        SELECT c.commentid, c.postid,c.commentimage,c.n_or_g, c.userid, u.username, c.text, c.commenteddate, u.profileimage
                        FROM groupcomment c
                        INNER JOIN user u ON c.userid = u.userid
                        WHERE c.postid = %s
                        ORDER BY c.commenteddate DESC
                        LIMIT %s
                        """,
                        (postid, commentslimit)
                    )

                records = await cursor.fetchall()

                if not records:
                    return JSONResponse(content={"comments": []}, status_code=200)

                serialized_records = serialize_record_comments(records)
                return JSONResponse(content={"comments": serialized_records}, status_code=200)

    except aiomysql.MySQLError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 
    
    







@app.get("/get_link_preview")
async def get_link_preview(url: str = Query(..., description="URL to fetch link preview")):
    try:
        # Ensure the URL has the correct schema (http or https)
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        
        # Send a GET request to the URL using the requests library
        response = requests.get(url)
        
        if response.status_code != 200:
            return JSONResponse(content={"error": "Unable to fetch URL"}, status_code=400)

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract Open Graph metadata
        title = soup.find("meta", property="og:title")
        description = soup.find("meta", property="og:description")
        image = soup.find("meta", property="og:image")
        
        # Prepare preview data
        preview_data = {
            "title": title["content"] if title else "No title available",
            "description": description["content"] if description else "No description available",
            "images": [image["content"]] if image else [],
            "url": url
        }

        return JSONResponse(content=preview_data, status_code=200)

    except Exception as e:
        print(f"Error fetching link preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch link preview")
    
    
    
    
    
  
    
    
    
    
    
    
    










@app.post("/update_comments")
async def update_comments(
    postid: int = Form(...),
    commentid: int = Form(...),
    edittextcomment: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "UPDATE comment SET text = %s WHERE commentid = %s AND postid = %s",
                    (edittextcomment, commentid, postid)
                )
                await conn.commit()

                if cursor.rowcount > 0:
                    return JSONResponse(content={"success": True, "message": "Comment updated successfully."}, status_code=200)
                else:
                    return JSONResponse(content={"success": False, "message": "No comment found to update."}, status_code=404)

    except aiomysql.MySQLDataError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=400, detail="Invalid data query")

    except aiomysql.MySQLError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    
    
    


@app.post("/update_comments_group")
async def update_comments_group(
    postid: int = Form(...),
    commentid: int = Form(...),
    edittextcomment: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "UPDATE groupcomment SET text = %s WHERE commentid = %s AND postid = %s",
                    (edittextcomment, commentid, postid)
                )
                await conn.commit()

                if cursor.rowcount > 0:
                    return JSONResponse(content={"success": True, "message": "Comment updated successfully."}, status_code=200)
                else:
                    return JSONResponse(content={"success": False, "message": "No comment found to update."}, status_code=404)

    except aiomysql.MySQLDataError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=400, detail="Invalid data query")

    except aiomysql.MySQLError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    
    
    
    
    
    
    
      
    
    
    
    
    



def serialize_record_replaycomments(record):
    """
    Serialize a single record (dictionary) or a list of records.
    Returns None if the record is None or empty.
    """
    if not record:
        return None
    
    if isinstance(record, dict):
        serialized_record = {}
        for key in record:
            if isinstance(record[key], datetime):
                serialized_record[key] = record[key].isoformat()
            elif isinstance(record[key], bytes):
                serialized_record[key] = base64.b64encode(record[key]).decode('utf-8')
            else:
                serialized_record[key] = record[key]
        return serialized_record
    
    elif isinstance(record, list):
        return [serialize_record(rec) for rec in record if rec]

    return None

@app.get("/get_replay_comments")
async def get_replay_comments(
    
    commentid: int = Query(...)
    
):
    try:
       
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM commentreply WHERE commentid = %s ORDER BY replayeddate DESC", 
                    (commentid,)
                )
                records = await cursor.fetchall()

                if not records:
                    return JSONResponse(content={"message": "No replay comments found"}, status_code=404)

                serialized_records = serialize_record_replaycomments(records)
                return JSONResponse(content={"replaycomments": serialized_records}, status_code=200)
    
    except aiomysql.MySQLDataError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=400, detail="Invalid data query")
    
    except aiomysql.MySQLError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=500, detail="Database error")
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    
    
    
    
    
    
    
    
def serialize_record_replaycomments_group(record):
    """
    Serialize a single record (dictionary) or a list of records.
    Returns None if the record is None or empty.
    """
    if not record:
        return None
    
    if isinstance(record, dict):
        serialized_record = {}
        for key in record:
            if isinstance(record[key], datetime):
                serialized_record[key] = record[key].isoformat()
            elif isinstance(record[key], bytes):
                serialized_record[key] = base64.b64encode(record[key]).decode('utf-8')
            else:
                serialized_record[key] = record[key]
        return serialized_record
    
    elif isinstance(record, list):
        return [serialize_record(rec) for rec in record if rec]

    return None

@app.get("/get_replay_comments_group")
async def get_replay_comments_group(
    
    commentid: int = Query(...)
    
):
    try:
    
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT  * from groupcommentreplay where commentid =%s ORDER BY replayeddate DESC", 
                    (commentid,)
                )
                records = await cursor.fetchall()

                if not records:
                    return JSONResponse(content={"message": "No replay comments found"}, status_code=404)

                serialized_records = serialize_record_replaycomments_group(records)
                return JSONResponse(content={"replaycomments": serialized_records}, status_code=200)
    
    except aiomysql.MySQLDataError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=400, detail="Invalid data query")
    
    except aiomysql.MySQLError as err:
        print(f"MySQL Error: {err}")
        raise HTTPException(status_code=500, detail="Database error")
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

 
    
    
    
    
def serialize_record_user(record):
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record


@app.post("/get_user_details")
async def get_user_details(userid: int = Form(...)):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM user WHERE userid=%s", (userid,))
            record = await cursor.fetchone()

            if record:
                record = serialize_record_user(record)
                return JSONResponse(content=record, status_code=200)
            else:
                return JSONResponse(content={"message": "User not found"}, status_code=404)
    

    
    
    
    
   
    




async def serialize_record_user_followlist(record):
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/get_userlist_to_follow")
async def get_userlist_to_follow(
    currentUserId: int = Form(...)
):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT otheruserid FROM iamfollowing WHERE myuserid = %s AND type = 'user'", (currentUserId,))
                followed_users = await cursor.fetchall()

                followed_user_ids = [user['otheruserid'] for user in followed_users]

                if followed_user_ids:
                    placeholders = ', '.join(['%s'] * len(followed_user_ids))
                    query = f"SELECT * FROM user WHERE userid NOT IN ({placeholders}) AND userid != %s LIMIT 20"
                    await cursor.execute(query, (*followed_user_ids, currentUserId))
                else:
                    await cursor.execute("SELECT * FROM user WHERE userid != %s LIMIT 20", (currentUserId,))
                
                user_details = await cursor.fetchall()

                if user_details:
                    serialized_user_details = [await serialize_record_user_followlist(user) for user in user_details]
                    return JSONResponse(content={"users": serialized_user_details}, status_code=200)
                else:
                    return JSONResponse(content={"message": "No users found"}, status_code=404)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
            
            
            
            
            
            
            
            
            
    
    
    
    
def serialize_record_group(record):
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/get_group_details")
async def get_group_details(groupid: str = Form(...)):
    try:
        async with pool.acquire() as conn:
            cursor = await conn.cursor(aiomysql.DictCursor)

       
            await cursor.execute("SELECT * FROM groups WHERE groupid = %s", (groupid,))
            group_record = await cursor.fetchone()

            if not group_record:
                return JSONResponse(content={"message": "Group not found"}, status_code=404)

            serialized_group = serialize_record_group(group_record)
 
            await cursor.execute("SELECT * FROM group_users WHERE groupid = %s ", (groupid))
            users_records = await cursor.fetchall()
 
            admin_users = [user for user in users_records if user['usertype'] == 'admin']
            non_admin_users = [user for user in users_records if user['usertype'] != 'admin']

            
            non_admin_users.sort(key=lambda user: user['joined_date'])

 
            serialized_admin_users = [serialize_record_group(user) for user in admin_users]
            serialized_non_admin_users = [serialize_record_group(user) for user in non_admin_users]

            await cursor.close()

        
            serialized_group['users'] = serialized_admin_users + serialized_non_admin_users

            return JSONResponse(content=serialized_group, status_code=200)

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
@app.post("/joined_or_not")
async def joined_or_not(
    groupid: str = Form(...),
    userid: str = Form(...),
):
    try:
        async with pool.acquire() as conn:
            cursor = await conn.cursor(aiomysql.DictCursor)

            await cursor.execute("SELECT * FROM group_users WHERE groupid = %s AND userid = %s", (groupid, userid))
            group_record = await cursor.fetchone()

            if not group_record:
                return JSONResponse(content={"message": "no"})

            return JSONResponse(content={"message": "yes"})

    except aiomysql.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
def serialize_search_result_user(record):
    """
    Serialize the user search result to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes) and key == 'profileimage':
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

def serialize_search_result_group(record):
    """
    Serialize the group search result to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes) and (key == 'groupimage' or key == 'groupbackgroundimage'):
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record
  
    
@app.post("/search-result")
async def search_result(query: str = Form(...)):
    """
    Search for users and groups where the username or groupname matches the query and return the results.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM user WHERE username LIKE %s", (f"%{query}%",))
                user_records = await cursor.fetchall()
                serialized_user_records = [serialize_search_result_user(record) for record in user_records]

                await cursor.execute("SELECT * FROM groups WHERE groupname LIKE %s", (f"%{query}%",))
                group_records = await cursor.fetchall()
                serialized_group_records = [serialize_search_result_group(record) for record in group_records]

                combined_results = {
                    "users": serialized_user_records,
                    "groups": serialized_group_records
                }

        return JSONResponse(content=combined_results, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
            
            













 
    
    
    
    
    
    
    
    
    
 



def serialize_search_enter_result_video(record):
    """
    Serialize the user search result to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            if key in ['userprofile', 'post']:   
                record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/search-enter-press-result")
async def search_enter_press_result(
    searchtext: str = Form(...),
    limit: int = Form(10),   
    offset: int = Form(0) 
    
    
):
    """
    Search for users whose username matches the query and return the results.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM post WHERE postdescription LIKE %s AND posttype ='video' ORDER BY posteddate DESC LIMIT %s OFFSET %s", 
                    (f"%{searchtext}%", limit, offset)
                )
                records = await cursor.fetchall()
                
                serialized_records = [serialize_search_enter_result_video(record) for record in records]
                
        return JSONResponse(content=serialized_records, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
 
 

 
 
 






 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
 
    
 
 
  
    
    
    
    
 
def serialize_post_record_viode_slider(record):
    """
    Serialize the post record to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            if key in [  'post' ,'userprofile']:   
                record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record



@app.get("/get_all_video_posts_slider")
async def get_all_video_posts_slider(limit: int = 5, offset: int = 0):
    """
    Get video posts from the database in batches of `limit`, starting at `offset`.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """
                    SELECT *
                    FROM post
                    WHERE posttype = 'video'
                    ORDER   BY RAND()
                    LIMIT %s OFFSET %s
                    """, (limit, offset)
                )
                records = await cursor.fetchall()
                
                serialized_records = [serialize_post_record_viode_slider(record) for record in records]
                
        return JSONResponse(content=serialized_records, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
           
        
            
            
            
@app.post("/search-enter-press-result-image-link-text")
async def search_enter_press_result_image_link_text(
    searchtext: str = Form(...),
    limit: int = Form(10),
    offset: int = Form(0)
):
    global pool
    searchtext = f"%{searchtext}%"  # Prepare for SQL LIKE query

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                # SQL query to search posts and calculate relevance based on the number of occurrences of searchtext
                query = """
                    SELECT *,
                    (LENGTH(postdescription) - LENGTH(REPLACE(postdescription, %s, ''))) / LENGTH(%s) AS relevance_desc,
                    (LENGTH(textbody) - LENGTH(REPLACE(textbody, %s, ''))) / LENGTH(%s) AS relevance_text
                    FROM post 
                    WHERE (posttype = 'text' OR posttype = 'link' OR posttype = 'image') 
                    AND (postdescription LIKE %s OR textbody LIKE %s)
                    ORDER BY relevance_desc DESC, relevance_text DESC
                    LIMIT %s OFFSET %s
                """
                await cursor.execute(query, (searchtext, searchtext, searchtext, searchtext, searchtext, searchtext, limit, offset))
                records = await cursor.fetchall()

                processed_records = []

                for record in records:
                    if record['posttype'] == 'image':
                        # Process image post with additional info
                        await cursor.execute("""
                            SELECT p.userid, p.username, p.postdescription, p.posteddate, p.userprofile, p.posttype, p.postid, p.n_or_g,
                                   p.groupname, p.groupid, p.grouptype, i.image
                            FROM post p
                            LEFT JOIN image i ON p.postid = i.postid
                            WHERE p.posttype = 'image' AND p.postid = %s 
                        """, (record['postid'],))
                        image_records = await cursor.fetchall()

                        for image_record in image_records:
                            if image_record['image']:
                                image_record['image'] = base64.b64encode(image_record['image']).decode('utf-8')
                            if image_record['userprofile']:
                                image_record['userprofile'] = base64.b64encode(image_record['userprofile']).decode('utf-8')

                            processed_records.append(image_record)

                    elif record['posttype'] in ['text', 'link']:
                        # Process text or link posts
                        post_record = {
                            'postid': record['postid'],
                            'userid': record['userid'],
                            'username': record['username'],
                            'postdescription': record['postdescription'],
                            'posteddate': record['posteddate'],
                            'posttype': record['posttype'],
                            'post': base64.b64encode(record['post']).decode('utf-8') if record['post'] else None,
                            'userprofile': base64.b64encode(record['userprofile']).decode('utf-8') if record['userprofile'] else None,
                            'filepath': record['filepath'] if 'filepath' in record else None,
                            'textcolor': record['textcolor'] if 'textcolor' in record else None,
                            'textbody': record['textbody'] if 'textbody' in record else None,
                            'thelink': record['thelink'] if 'thelink' in record else None,
                            'groupid': record['groupid'] if 'groupid' in record else None,
                            'grouptype': record['grouptype'] if 'grouptype' in record else None,
                            'n_or_g': record['n_or_g'] if 'n_or_g' in record else None,
                            'groupname': record['groupname'] if 'groupname' in record else None,
                        }

                        processed_records.append(post_record)

                return processed_records

            except aiomysql.Error as err:
                print(f"Error: {err}")
                raise HTTPException(status_code=500, detail="Internal Server Error")
            
            
            
            
            
            
            
             
    
    




@app.post("/check_groupname_exsist_or_not_group")
async def check_groupname_exsist_or_not_group(
    groupname: str = Form(...)
):
    """
    Check if a groupname exists in the database and return a message.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = """
                SELECT groupname FROM groups 
                WHERE groupname = %s
                """
                await cursor.execute(query, (groupname,))
                record = await cursor.fetchone()  
                
                if record:
                    return {"message": "yes"}
                else:
                    return {"message": "no"}

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    






    
    
    
    
    
    
    
    
    
    
    
    
    
    



    
    
    
    
    
    
    
    
    
     
     
     
     



def serialize_search_enter_result_group(record: dict) -> dict:
    """
    Serialize the user search result to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes) and key in ['groupimage', 'groupbackgroundimage']:
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/search-enter-press-get-groups")
async def search_enter_press_get_groups(
    
    searchtext: str = Form(...),
    limit: int = Form(10),   
    offset: int = Form(0) 
    
    
    ):
    """
    Search for users where the username matches the query and return the results.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = """
                SELECT * FROM groups 
                WHERE groupname LIKE %s
                ORDER BY createdate DESC
                 LIMIT %s OFFSET %s
                """
                await cursor.execute(query, (f"%{searchtext}%", limit, offset))
                records = await cursor.fetchall()
                
                serialized_records = [serialize_search_enter_result_group(record) for record in records]
                
        return JSONResponse(content=serialized_records, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    





def serialize_search_enter_result_user_textlink(record):
    """
    Serialize the user search result to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes):
            if key in ['userprofile', 'post']: 
                record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/search-enter-press-result-link-text")
async def search_enter_press_result_link_text(
    searchtext: str = Form(...),
    limit: int = Form(10),   
    offset: int = Form(0) 
    
    ):
    """
    Search for posts where the description or body matches the query and return the results.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
              
                query = """
                SELECT * FROM post 
                WHERE (posttype = 'text' OR posttype = 'link') 
                AND (postdescription LIKE %s OR textbody LIKE %s)  ORDER BY posteddate DESC
                LIMIT %s OFFSET %s
                """
                await cursor.execute(query, (f"%{searchtext}%", f"%{searchtext}%", limit, offset))
                records = await cursor.fetchall()
                
                serialized_records = [serialize_search_enter_result_user_textlink(record) for record in records]
                
        return JSONResponse(content=serialized_records, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
def serialize_search_enter_result_user(record: dict) -> dict:
    """
    Serialize the user search result to handle datetime and bytes data types.
    """
    for key in record:
        if isinstance(record[key], datetime):
            record[key] = record[key].isoformat()
        elif isinstance(record[key], bytes) and key == 'profileimage':
            record[key] = base64.b64encode(record[key]).decode('utf-8')
    return record

@app.post("/search-enter-press-get-users")
async def search_enter_press_get_users(
    searchtext: str = Form(...),
     limit: int = Form(10),   
    offset: int = Form(0) 
    
    
    ):
    """
    Search for users where the username matches the query and return the results.
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = """
                SELECT * FROM user 
                WHERE username LIKE %s
                ORDER BY createddate DESC
                LIMIT %s OFFSET %s
                """
                await cursor.execute(query, (f"%{searchtext}%", limit, offset))
                records = await cursor.fetchall()
                
                serialized_records = [serialize_search_enter_result_user(record) for record in records]
                
        return JSONResponse(content=serialized_records, status_code=200)

    except aiomysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    
    
    
    
    
    

















    
           
            
@app.get("/delete_comment")
async def delete_comment(
    commentid: int = Query(...)
):
    """
    Delete a comment by its ID.

    Args:
    commentid (int): The ID of the comment to be deleted.

    Returns:
    JSONResponse: A JSON response indicating the result of the deletion.
    """
    try:
        global pool
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM comment WHERE commentid=%s", (commentid,))
                await conn.commit()

        return JSONResponse(content={"message": "Deleted"}, status_code=200)
    except Exception as e:
 
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
    
    





    
    
    
    
    
    
    
@app.post("/start-to-follow")
async def update_user_details(
    iamfollowinguserid: str = Form(...),
    myuserid: str = Form(...),
):
    global pool
    createddate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                
                await cursor.execute("SELECT * FROM user WHERE userid=%s", (iamfollowinguserid,))
                iamfollowing_user = await cursor.fetchone()
                
                if not iamfollowing_user:
                    raise HTTPException(status_code=404, detail=f"User with userid {iamfollowinguserid} not found")
                
                await cursor.execute("SELECT * FROM user WHERE userid=%s", (myuserid,))
                my_user = await cursor.fetchone()
                
                if not my_user:
                    raise HTTPException(status_code=404, detail=f"User with userid {myuserid} not found")
                
                await cursor.execute("SELECT * FROM iamfollowing WHERE otheruserid=%s AND myuserid=%s", 
                                     (iamfollowing_user['userid'], my_user['userid']))
                iamfollowing_exists = await cursor.fetchone()
                
                await cursor.execute("SELECT * FROM iamfollowed WHERE otheruserid=%s AND myuserid=%s", 
                                     (my_user['userid'], iamfollowing_user['userid']))
                iamfollowed_exists = await cursor.fetchone()
                
                if iamfollowing_exists or iamfollowed_exists:
                    if iamfollowing_exists:
                        await cursor.execute("DELETE FROM iamfollowing WHERE otheruserid=%s AND myuserid=%s AND type='user'", 
                                             (iamfollowing_user['userid'], my_user['userid']))
                    if iamfollowed_exists:
                        await cursor.execute("DELETE FROM iamfollowed WHERE otheruserid=%s AND myuserid=%s", 
                                             (my_user['userid'], iamfollowing_user['userid']))
                    await conn.commit()
                    return JSONResponse(content={"message": "Records already existed and were deleted"}, status_code=200)
                
                await cursor.execute("""
                    INSERT INTO iamfollowing (myuserid, otheruserid, username, profile,date,type)
                    VALUES (%s, %s, %s, %s,%s,%s)
                """, (myuserid, iamfollowing_user['userid'], iamfollowing_user['username'], iamfollowing_user['profileimage'],createddate,'user'))
                
                await cursor.execute("""
                    INSERT INTO iamfollowed (myuserid, otheruserid, username, profile,date)
                    VALUES (%s, %s, %s, %s,%s)
                """, (iamfollowinguserid, my_user['userid'], my_user['username'], my_user['profileimage'],createddate))
                
                # Commit the transaction
                await conn.commit()

                return JSONResponse(content={"message": "User details updated successfully"}, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"message": f"Internal Server Error: {str(e)}"}, status_code=500)
    
    
    
    
    
 
 
 
    
    
 

 

  
  


 
     
