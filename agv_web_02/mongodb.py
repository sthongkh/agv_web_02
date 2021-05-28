import pymongo
import re


class MongoDB():

    def __init__(self):
        self.myclient = pymongo.MongoClient("mongodb://planagv:27017/")
        self.mydb = self.myclient["agv"]

    def check_user(self, user, pw):
        col = self.mydb["user"]
        query = {"user_name" : "{}".format(user)}
        res = col.find_one(query)["password"]
        id = col.find_one(query)["_id"]
        print(id)
        return (pw == res)

    def match_user(self, user, pw):
        col = self.mydb["user"]
        query = {"user_name" : "{}".format(user)}
        res = col.find_one(query)
        if res != None:
            res_pw = res["password"]
            if pw == res_pw:
                return str(res["_id"]), res["plant"]
                
            return False, 0

        else:
            return False, 0


    def get_all_station(self, plant):
        col = self.mydb["station"]
        query = {"plant" : plant}
        res = col.find(query)
        sid = []
        sname = []
        for x in res:
            sid.append(x["station_id"])
            sname.append(x["station_name"])

        return sid, sname

    def get_queue_agv(self, agv_num, user=None):
        col = self.mydb["queue_agv_{}".format(agv_num)]
        if user != None:
            query = {"user" : user}

        else:
            query = {}

        res = col.find(query)
        data = []

        for x in res:
            data.append(x)

        return data

    def get_agv_num(self):
        res = self.mydb.list_collection_names()
        ret = []
        for i in res:
            match = re.match("queue_agv_(\d+)", i)
            if match:
                ret.append("{:02d}".format(int(match.group(1))))

        return ret

    def add_queue(self, agv_num, data_dict):
        col = self.mydb["queue_agv_{}".format(agv_num)]
        ret = col.insert_one(data_dict)
        return (False, True)[ret != None]

    def del_queue(self, agv_num, index):
        col = self.mydb["queue_agv_{}".format(agv_num)]
        query = { "_id":  index}
        ret = col.delete_one(query)
        return (False, True)[ret != None]

    def get_mapping_agv(self, plant_num):
        col = self.mydb["mapping_agv"]
        query = {}
        res = col.find_one(query)
        res = res["plant{}".format(plant_num)]
        return res

    def get_queue_number_max_agv(self, agv_num):
        col = self.mydb["queue_agv_{}".format(agv_num)]
        query = {}
        res = col.find(query)
        data = [0]
        for i in res:
            data.append(i["queue"])

        return max(data)


    def test(self, text):
        print(text)







