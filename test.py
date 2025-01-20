 letter_string = generate_random_letter_string()
post_id = generate_combined_post_id(letter_string)
        
        
letter_string_group_post = generate_random_letter_string()
post_id_group_post = generate_combined_post_id(letter_string_group_post)







@app.post("/add-post-image")
async def add_post(
    uid: int = Form(...),
    imagePostdescription: str = Form(...),
    imagefile: list[UploadFile] = File(...),
    current_user: str = Depends(get_current_user)
):
    createddate = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    cursor = conn.cursor(dictionary=True)
    
    try:
        if str(current_user) != str(uid):
            raise HTTPException(status_code=401, detail="Unauthorized access")
        
        cursor.execute("SELECT username, profileimage FROM user WHERE userid = %s", (uid,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        username = user['username']
        userprofile = user.get('profileimage', None)
        letter_string = generate_random_letter_string()
        post_id = generate_combined_post_id(letter_string)

        first_image_data = None
        if len(imagefile) > 0 and imagefile[0].content_type.startswith('image'):
            first_image_data = await imagefile[0].read()

       
        cursor.execute(
            """
            INSERT INTO post (postid, userid, username, postdescription, posteddate, posttype, post, userprofile)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (post_id, uid, username, imagePostdescription, createddate, 'image', first_image_data, userprofile)
        )
        conn.commit()

      
        for index, file in enumerate(imagefile):
            if file.content_type.startswith('image'):
                if index == 0:
                    media_data = first_image_data
                else:
                    media_data = await file.read()
                
                cursor.execute(
                    """
                    INSERT INTO image (postid, image)
                    VALUES (%s, %s)
                    """,
                    (post_id, media_data)
                )

        conn.commit()
    except pymysql.Error as err:
        print(f"Database error: {err}")
        raise HTTPException(status_code=500, detail="Error storing image post in database")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")
    finally:
        cursor.close()

    return JSONResponse(content={"message": "Post added successfully"}, status_code=201)
