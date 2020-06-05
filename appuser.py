# -----------------------------------------------------------------------------
#
# Class AppUser - Class being made for the User of the App.
# Contains  fname - Firstname, lname - Last Name, email - Email Address
#           uid - Unique Identification Number, password - password
#
# -----------------------------------------------------------------------------


class AppUser:
    def __init__(self,fname,lname,email,uid,password):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.uid = uid
        self.password = password

    def __str__(self):
        return f'{self.uid} {self.fname} {self.lname} {self.email}'
