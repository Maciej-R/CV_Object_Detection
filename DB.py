import sqlite3 as sql
from pathlib import Path
from hashlib import sha3_256
import unittest


class DataBase:

    db_path = "JPWP.db"
    create = False
    if not Path(db_path).is_file():
        create = True
    db = sql.connect(db_path)
#   Create date base if it doesn't exist
    if create:

        db.execute('''
                    create table general(
                    image_id integer primary key,
                    path text unique,
                    hash varchar(64)) 
                    ''')

        db.execute('''
                    create table tags(
                    tag_id integer primary key,
                    title text);
                    ''')

        db.execute('''
                    create table image_tags(
                    image_id integer,
                    tag_id integer,
                    foreign key (image_id) references general(image_id),
                    foreign key (tag_id) references tags(tag_id))
                    ''')

        db.commit()

    autocommit = False

    @staticmethod
    def set_autocommit(b):
        """
        Commit after adding images/tags
        :param b: Boolean
        """
        DataBase.autocommit = b

    @staticmethod
    def get_image_tags(*, image_id=None, pth=None):
        """
        Use one of (image_id, path)
        :param pth: Path to image
        :param image_id: Image ID
        :return: Tags of image
        """

        #One can be chosen
        if image_id is not None and pth is not None:
            raise AttributeError

#       If path given, get id
        if pth is not None:
            image_id = DataBase.db.execute(f"select (image_id) from general where path = ('{pth}')").fetchall()[0][0]

#       Get id of relevant tags
        tags_id = DataBase.db.execute(f"select (tag_id) from image_tags where image_id = {image_id}").fetchall()
#       Check if any present
        if len(tags_id) < 1:
            return None
#       String list of tag ids
        id_str = ''
        for i in range(len(tags_id)-1):
            id_str = id_str + str(tags_id[i][0]) + ', '
        id_str += str(tags_id[len(tags_id)-1][0])
#       Get result
        res = DataBase.db.execute(f"select (title) from tags where tag_id in ({id_str});").fetchall()
#       List from list of tuples
        tags_str = list()
        for tag in res:
            tags_str.append(tag[0])

        return tags_str

    @staticmethod
    def get_tagged_items(tag_title):
        """
        :param tag_title: Search tag title
        :return: Id of images with given tag
        """

        tid = DataBase.db.execute(f"select (tag_id) from tags where title = '{tag_title}' limit 1").fetchall()
#       Tag doesn't exist
        if len(tid) < 1:
            return list()
        tid = tid[0][0]
        id_list = DataBase.db.execute(f"select (image_id) from image_tags where tag_id = {tid}").fetchall()
        res = list()
#       Tag present but not images with it
        if len(id_list) < 1:
            return res
#       Get ids from list of tuples
        else:
            for t in id_list:
                res.append(t[0])
        return res

    @staticmethod
    def tag_image(tag, *, image_id=None, pth=None):
        """
        Use image_id or path
        :param tag: Tag title
        :param image_id: Image id
        :param pth: Path to image
        """

#       Only one of options allowed
        if pth is None and image_id is None:
            raise AttributeError
        if image_id is not None and pth is not None:
            raise AttributeError

#       Tag id
        tid = DataBase.db.execute(f"select (tag_id) from tags where title = ('{tag}') limit 1").fetchall()
        tag_absent = len(tid) < 1

#       If tag is new add it to tags table
        if tag_absent:
            DataBase.db.execute(f"insert into tags (title) values('{tag}');")
            tid = DataBase.db.execute(f"select (tag_id) from tags where title = ('{tag}') limit 1;").fetchall()[0][0]
        else:
            tid = tid[0][0]

#       If path was given get id
        if image_id is None:
            image_id = DataBase.db.execute(f"select (image_id) from general where path = ('{pth}')").fetchall()[0][0]

#       Tag
        DataBase.db.execute(f"insert into image_tags (image_id, tag_id) values ({image_id}, {tid});")

        if DataBase.autocommit:
            DataBase.db.commit()

    @staticmethod
    def untag_image(image_id, tag_id):

        DataBase.db.execute(f"delete from image_tags where image_id = {image_id} and tag_id = {tag_id}")

    @staticmethod
    def add_image(path):
        """
        Add image from given path
        :param path: Path to image
        """

#       Calculate file haah
        with open(path, "rb") as f:
            bts = f.read()
        sha3 = sha3_256()
        sha3.update(bts)
        shash3 = sha3.digest()

        DataBase.db.execute(f"insert into general (path, hash) values ('{path}', '{shash3.hex()}')")

        if DataBase.autocommit:
            DataBase.db.commit()

    @staticmethod
    def get_tag_id(title):
        """
        :param title: Tag title
        :return: Tag id
        """

        try:
            res = DataBase.db.execute(f"select (tag_id) from tags where title = {title}").fetchall()[0][0]
        except sql.OperationalError:
            res = list()
        return res


    @staticmethod
    def get_path(image_id):
        """
        :param image_id:
        :return: Path to image with image_id
        """

        return DataBase.db.execute(f"select (path) from general where image_id = {image_id}").fetchall()[0][0]


class Test(unittest.TestCase):

    def testDB(self):

        #Is table empty
        self.assertTrue(len(DataBase.db.execute("select * from general").fetchall()) == 0)
#       Add example images
        pth = "images\\"
        DataBase.add_image(pth + "example_01.jpg")
        DataBase.add_image(pth + "example_02.jpg")
        DataBase.add_image(pth + "example_03.jpg")
#       No path duplicates
        with self.assertRaises(sql.IntegrityError):
            DataBase.add_image(pth + "example_03.jpg")
#       Images and paths added
        self.assertTrue(len(DataBase.db.execute("select * from general").fetchall()) == 3)
#        self.assertTrue(len(DataBase.db.execute("select * from images").fetchall()) == 3)
#       Empty tags table
        self.assertTrue(len(DataBase.db.execute("select * from tags").fetchall()) == 0)
        DataBase.tag_image(1, "test")
#       Check creation of new tag
        self.assertTrue(len(DataBase.db.execute("select * from tags").fetchall()) == 1)
#       Not existing tag
        self.assertEqual(len(DataBase.get_tag_id("Not_exisitng")), 0)



if __name__ == "__main__":

    unittest.main()

    pass
