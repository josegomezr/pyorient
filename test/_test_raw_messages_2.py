__author__ = 'Ostico <ostico@gmail.com>'

import sys
import unittest
import os

os.environ['DEBUG'] = "1"
os.environ['DEBUG_VERBOSE'] = "0"
if os.path.realpath( '../' ) not in sys.path:
    sys.path.insert( 0, os.path.realpath( '../' ) )

if os.path.realpath( '.' ) not in sys.path:
    sys.path.insert( 0, os.path.realpath( '.' ) )

from pyorient.utils import *
from pyorient.Messages.Constants.OrientPrimitives import *
from pyorient.OrientException import *
from pyorient.Messages.OrientSocket import OrientSocket
from pyorient.Messages.Server.ConnectMessage import ConnectMessage
from pyorient.Messages.Server.DbExistsMessage import DbExistsMessage
from pyorient.Messages.Server.DbOpenMessage import DbOpenMessage
from pyorient.Messages.Server.DbCreateMessage import DbCreateMessage
from pyorient.Messages.Server.DbDropMessage import DbDropMessage
from pyorient.Messages.Server.DbReloadMessage import DbReloadMessage
from pyorient.Messages.Server.ShutdownMessage import ShutdownMessage
from pyorient.Messages.Server.DbCountRecordsMessage import DbCountRecordsMessage

from pyorient.Messages.Database.DbCloseMessage import DbCloseMessage
from pyorient.Messages.Database.DbSizeMessage import DbSizeMessage
from pyorient.Messages.Database.SQLCommandMessage import SQLCommandMessage
from pyorient.Messages.Database.RecordLoadMessage import RecordLoadMessage
from pyorient.Messages.Database.RecordCreateMessage import RecordCreateMessage
from pyorient.Messages.Database.RecordUpdateMessage import RecordUpdateMessage
from pyorient.Messages.Database.RecordDeleteMessage import RecordDeleteMessage
from pyorient.Messages.Database.DataClusterCountMessage import DataClusterCountMessage
from pyorient.Messages.Database.DataClusterDataRangeMessage import DataClusterDataRangeMessage
from pyorient.ORecordCoder import *

class CommandTestCase(unittest.TestCase):
    """ Command Test Case """
    
    def test_record_load(self):
        connection = OrientSocket( "localhost", int( 2424 ) )

        # print "Sid, should be -1 : %s" % connection.session_id
        assert connection.session_id == -1

        # ##################

        msg = DbOpenMessage( connection )

        db_name = "GratefulDeadConcerts"
        cluster_info = msg.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()
        assert len(cluster_info) != 0

        req_msg = RecordLoadMessage( connection )

        res = req_msg.prepare( [ "#11:0", "*:-1" ] ) \
            .send_message().fetch_response()

        assert res.rid == "#11:0"
        assert res.o_class == 'followed_by'
        assert res.__getattribute__('in') != 0
        assert res.out != 0

        # print res
        # print "%r" % res.rid
        # print "%r" % res.o_class
        # print "%s" % res.__getattribute__('in')
        # print "%s" % res.out


    def test_record_count_with_no_opened_db(self):
        connection = OrientSocket( "localhost", int( 2424 ) )

        # print "Sid, should be -1 : %s" % connection.session_id
        assert connection.session_id == -1

        # ##################
        conn_msg = ConnectMessage( connection )
        # print "Protocol: %r" % conn_msg.get_protocol()
        session_id = conn_msg.prepare( ("admin", "admin") )\
            .send_message().fetch_response()

        # print "Sid: %s" % session_id
        assert session_id == connection.session_id
        assert session_id != -1

        try:
            count_msg = DbCountRecordsMessage( connection )
            res = count_msg.prepare().send_message().fetch_response()
            assert False  # we expect an exception because we need a db opened
        except PyOrientDatabaseException:
            assert True


    def test_record_count(self):
        connection = OrientSocket( "localhost", int( 2424 ) )

        # print "Sid, should be -1 : %s" % connection.session_id
        assert connection.session_id == -1

        # ##################

        msg = DbOpenMessage( connection )

        db_name = "GratefulDeadConcerts"
        cluster_info = msg.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()
        assert len(cluster_info) != 0

        session_id = connection.session_id
        assert session_id != -1
        # print "Sid: %s" % session_id
        assert session_id != -1

        count_msg = DbCountRecordsMessage( connection )
        res = count_msg.prepare().send_message().fetch_response()

        # print res
        assert res is not 0
        assert res > 0


    def test_record_create_update(self):

        connection = OrientSocket( "localhost", int( 2424 ) )
        conn_msg = ConnectMessage( connection )
        # print "Protocol: %r" % conn_msg.get_protocol()
        assert connection.protocol != -1

        session_id = conn_msg.prepare( ("admin", "admin") ) \
            .send_message().fetch_response()

        # print "Sid: %s" % session_id
        assert session_id == connection.session_id
        assert session_id != -1

        # ##################

        db_name = "my_little_test"

        msg = DbExistsMessage( connection )
        exists = msg.prepare( [db_name] ).send_message().fetch_response()

        print "Before %r" % exists
        if exists is False:
            print "Creation"
            try:
                ( DbCreateMessage( connection ) ).prepare(
                    (db_name, DB_TYPE_DOCUMENT, STORAGE_TYPE_PLOCAL)
                ).send_message().fetch_response()
                assert True
            except PyOrientCommandException, e:
                print e.message
                assert False  # No expected Exception

        msg = DbOpenMessage( connection )
        cluster_info = msg.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()
        # print cluster_info
        assert len(cluster_info) != 0

        rec = { 'alloggio': 'casa', 'lavoro': 'ufficio', 'vacanza': 'mare' }
        rec_position = ( RecordCreateMessage(connection) )\
            .prepare( ( 1, rec ) )\
            .send_message().fetch_response()

        # print rec_position
        assert rec_position[0] != 0

        rec = { 'alloggio': 'albergo', 'lavoro': 'ufficio', 'vacanza': 'montagna' }
        update_success = ( RecordUpdateMessage(connection) )\
            .prepare( ( 1, rec_position[0], rec ) )\
            .send_message().fetch_response()

        # print update_success
        assert update_success[0] != 0

        res = ( SQLCommandMessage( connection ) )\
            .prepare( [ QUERY_SYNC, "select from #1:" + str(rec_position[0]) ] )\
            .send_message().fetch_response()

        # print "%r" % res[0].rid
        # print "%r" % res[0].o_class
        # print "%r" % res[0].version
        # print "%r" % res[0].alloggio
        # print "%r" % res[0].lavoro
        # print "%r" % res[0].vacanza

        assert res[0].rid == '#1:2'
        assert res[0].o_class is None
        # assert res[0].version == 1
        assert res[0].alloggio == 'albergo'
        assert res[0].lavoro == 'ufficio'
        assert res[0].vacanza == 'montagna'

        # at the end drop the test database
        ( DbDropMessage( connection ) ).prepare([db_name]) \
            .send_message().fetch_response()


    def test_record_delete(self):

        connection = OrientSocket( "localhost", int( 2424 ) )

        conn_msg = ConnectMessage( connection )
        assert connection.protocol != -1

        session_id = conn_msg.prepare( ("admin", "admin") ) \
            .send_message().fetch_response()

        print "Sid: %s" % session_id
        assert session_id == connection.session_id
        assert session_id != -1

        db_name = "my_little_test"

        msg = DbExistsMessage( connection )
        exists = msg.prepare( [db_name] ).send_message().fetch_response()

        print "Before %r" % exists
        if exists is False:
            print "Creation"
            try:
                ( DbCreateMessage( connection ) ).prepare(
                    (db_name, DB_TYPE_DOCUMENT, STORAGE_TYPE_PLOCAL)
                ).send_message().fetch_response()
                assert True
            except PyOrientCommandException, e:
                print e.message
                assert False  # No expected Exception

        msg = DbOpenMessage( connection )
        cluster_info = msg.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()

        assert len(cluster_info) != 0

        rec = { 'alloggio': 'casa', 'lavoro': 'ufficio', 'vacanza': 'mare' }
        rec_position = ( RecordCreateMessage(connection) )\
            .prepare( ( 1, rec ) )\
            .send_message().fetch_response()

        print rec_position
        assert rec_position[0] != 0

        ######################## Check Success
        res = ( SQLCommandMessage( connection ) )\
            .prepare( [ QUERY_SYNC, "select from #1:" + str(rec_position[0]) ] )\
            .send_message().fetch_response()

        # print "%r" % res[0].rid
        # print "%r" % res[0].o_class
        # print "%r" % res[0].version
        # print "%r" % res[0].alloggio
        # print "%r" % res[0].lavoro
        # print "%r" % res[0].vacanza

        assert res[0].rid == '#1:2'
        assert res[0].o_class is None
        # assert res[0].version == 0
        assert res[0].alloggio == 'casa'
        assert res[0].lavoro == 'ufficio'
        assert res[0].vacanza == 'mare'

        ######################## Delete Rid

        del_msg = (RecordDeleteMessage(connection))
        deletion = del_msg.prepare( ( 1, rec_position[0] ) ).send_message()\
            .fetch_response()

        assert deletion is True

        # now try a failure in deletion for wrong rid
        del_msg = (RecordDeleteMessage(connection))
        deletion = del_msg.prepare( ( 1, 11111 ) ).send_message()\
            .fetch_response()

        assert deletion is False

        # at the end drop the test database
        ( DbDropMessage( connection ) ).prepare([db_name]) \
            .send_message().fetch_response()


    def test_data_cluster_count(self):

        connection = OrientSocket( "localhost", int( 2424 ) )
        assert connection.session_id == -1

        # ##################

        msg = DbOpenMessage( connection )

        db_name = "GratefulDeadConcerts"
        cluster_info = msg.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()

        print cluster_info
        assert len(cluster_info) != 0
        assert connection.session_id != -1

        count_msg = DataClusterCountMessage( connection )
        res1 = count_msg.set_count_tombstones(1)\
            .prepare( [ range(0, 11) ] ).send_message().fetch_response()

        print res1
        assert res1 is not 0
        assert res1 > 0

        count_msg = DataClusterCountMessage( connection )
        res2 = count_msg.set_count_tombstones(1)\
            .prepare( [ range(0, 11), 1 ] ).send_message().fetch_response()

        print res2
        assert res2 is not 0
        assert res2 > 0

        count_msg = DataClusterCountMessage( connection )
        res3 = count_msg.set_count_tombstones(1).set_cluster_ids( range(0, 11) )\
            .prepare().send_message().fetch_response()

        print res3
        assert res3 is not 0
        assert res3 > 0

        assert res1 == res2
        assert res3 == res2
        assert res3 == res1

    def test_query_async(self):
        connection = OrientSocket( 'localhost', 2424 )
        open_msg = DbOpenMessage(connection)

        open_msg.set_db_name('GratefulDeadConcerts')\
            .set_user('admin').set_pass('admin').prepare()\
            .send_message().fetch_response()

        try_select_async = SQLCommandMessage(connection)

        try_select_async.set_command_type(QUERY_ASYNC)\
                        .set_query("select from followed_by")\
                        .set_limit(50)\
                        .set_fetch_plan("*:0")\
                        .prepare()\
                        .send_message()

        response = try_select_async.fetch_response()

        assert response is not []
        assert response[0].rid is not None  # assert no exception
        assert response[1].rid is not None  # assert no exception
        assert response[2].rid is not None  # assert no exception
        # for x in response:
        #     print x
        #     print x.rid
        #     print x.o_class
        #     print x.__getattribute__('in')
        #     print x.out

    def test_wrong_data_range(self):
        connection = OrientSocket( 'localhost', 2424 )

        db_name = "GratefulDeadConcerts"

        db = DbOpenMessage(connection)
        cluster_info = db.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()

        datarange = DataClusterDataRangeMessage(connection)
        try:
            value = datarange.prepare(32767).send_message().fetch_response()
        except PyOrientCommandException, e:
            assert e.message == "32767 - java.lang.ArrayIndexOutOfBoundsException"

    def test_data_range(self):
        connection = OrientSocket( 'localhost', 2424 )

        db_name = "GratefulDeadConcerts"

        db = DbOpenMessage(connection)
        cluster_info = db.prepare(
            (db_name, "admin", "admin", DB_TYPE_DOCUMENT, "")
        ).send_message().fetch_response()

        # print cluster_info

        cluster_info.sort(key=lambda cluster: cluster['id'])

        for cluster in cluster_info:
            # os.environ['DEBUG'] = '0'  # silence debug
            datarange = DataClusterDataRangeMessage(connection)
            value = datarange.prepare(cluster['id']).send_message().fetch_response()
            print "Cluster Name: %s, ID: %u: %s " \
                  % ( cluster['name'], cluster['id'], value )
            assert value is not []
            assert value is not None


# test_record_load()
# test_record_count_with_no_opened_db()
# test_record_count()
# test_record_create_update()
# test_record_delete()
# test_data_cluster_count()
# test_query_async()
# test_wrong_data_range()
# test_data_range()