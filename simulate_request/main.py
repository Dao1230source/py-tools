from simulate_request.data_parser import DataParser
from simulate_request.data_source import FileDataSource, InputDataSource
from simulate_request.helper import SimulateRequest
from simulate_request.request_executor import RemoteRequestExecutor, CurlRequestExecutor
from utils.base_util import stats_time
from context import ContextIms, ContextEwms, ContextMscpOM


@stats_time(name="execute_request")
def execute_request(db_request_context):
    simulate_request = SimulateRequest(db_request_context)
    # 执行前打开文件，保存下
    """
    配置数据来源参数
    """
    data_source = FileDataSource(
        file_path=r'G:\01404679\document\生产问题\2024\202412\20241224\采购关闭.xlsx',
        sheet_name='Sheet0',
        # 针对值是0开头的列配置，比如：员工工号
        converters={r'员工工号': str})
    # sql = '''
    #     select demand_id,from_warehouse_code,materiel_code,remark2,numbers, plan_type,order_type,area_code
    #     from tm_order_inventory_allocation
    #     where from_warehouse_code = '532DMB' and materiel_code = '430100100116'
    #     limit 1
    #     '''
    # data_source = SqlDataSource(sql, context.database)
    # input_data = [
    #     {"warehouse_code": "595DMB", "sku_no": "430400203399", "inventory_status": "10", "companyCode": "C201",
    #      "company_code": "C201",
    #      "demand_id": "BF23071409260639", "amount": 100.000000, "type": "VALUE", "order_type": 13,
    #      "collect_id": "PJ202205068809031_4", "area_code": "852Y", "deliver_address": "2", "policy_id": "SF",
    #      "remark1": "PJ202205068809031", "cgId": "PP23030300000221", "asnId": "ASN230220000866-3201",
    #      "onWayId": "PP23021500000420", "uniqueId": "106163428", "availableGap": -7288,
    #      "availableMustPositiveOrZero": False, "syncTime": "2023-07-27T00:00:00"}
    # ]
    # mscp
    # {
    #     "mapperName": "employeeMapper",
    #     "selectColumnName": "emp_code", "values": None,
    #     "encryptColumnName": "phone_num", "encryptFieldName": "phoneNum", "dataType": "PHONE_NUMBER",
    #     "text": " ", "texts": ["18312476556"], "resultType": "DESENSITIZED", "userId": "01404679"
    # }
    # ]
    # redisSet
    # input_data = {"type": 'PUBLISH', 'key': 'CONFIG_REFRESH', 'value': 'GROUP_INVENTORY_STATUS'}
    # input_data = {"type": 'SCAN', 'key': 'opc_im_*_demand_allot_key'}
    # input_data = {"type": 'DELETE', 'key': 'opc_im_{SCM008_440200301161_10_C201}_demand_allot_key'}
    # data_source = InputDataSource(input_data)
    simulate_request.set_data_source(data_source=data_source)
    """
    ims
    inventoryRefreshPoolBatch, scheduleBalanceExecute, scheduleInventoryCheck, inventorySummary,
    demandOperateCancelBatch, demandOperateFinishBatch, demandOperateDelivery, demandOperateDeliveryBatch,
    demandMatchBatch, demandMatchExecute, analyseDemandIsEnough, asnSync, onWayDelBatch, 
    stockApprove, stockReview, inventoryFreeze, inventoryUpdate, redisSet, redisGet, groupSkuSelect
    # opc-web
    demand/batch/outWarehouse/pullback, exceptionConfirm, demand/outWarehouse/modify, whcodeMonthcard/addWhcodeMonthcard
    # e wms
    syncInventoryData
    # mscp - datasource
    syncWarehouse,manualEncrypt
    # mscp - encryptor
    encryptBatch,decryptBatchAsMap
    # mscp - om
    inSubmitAndConfirm
    """
    data_parser = DataParser(request_name='demandOperateCancelBatch')
    simulate_request.set_data_parser(data_parser=data_parser)
    """
    配置请求执行参数
    """
    # request_executor = CurlRequestExecutor(request_context=db_request_context.request)
    request_executor = RemoteRequestExecutor(request_context=db_request_context.request)
    simulate_request.set_request_executor(request_executor=request_executor)
    """
    正式执行
    """
    simulate_request.set_extra_funcs({
        'pullReason': lambda f: setattr(f, 'default', '需求拉回，重新下发。请联系李皇华（180529）'),
        'orderType': lambda f: setattr(f, 'default', 33),
        'unlockDemandAllotLockKey': lambda f: setattr(f, 'default', True),
        'unlockGroupedDemandAllotLockKeys': lambda f: setattr(f, 'default', True),
        'status': lambda f: setattr(f, 'default', 2),
    })
    simulate_request.set_batch_size(batch_size=100)
    simulate_request.set_thread_nums(thread_nums=1)
    simulate_request.set_headers({
        'Cookie': 'MSCP-TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3MTU4NTc0ODgsImV4cCI6MTcxNTg2NDY4OCwidXNlcklkIjoiMDE0MDQ2NzkifQ.eb252P4Xzq_flWbmwqHysWfch9aSvwNIpF0qCWXuD3o; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218f81137bac581-078afdd2a11d6d8-26001d51-2073600-18f81137bad11db%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThmODExMzdiYWM1ODEtMDc4YWZkZDJhMTFkNmQ4LTI2MDAxZDUxLTIwNzM2MDAtMThmODExMzdiYWQxMWRiIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218f81137bac581-078afdd2a11d6d8-26001d51-2073600-18f81137bad11db%22%7D; sajssdk_2015_cross_new_user=1',
        'X-User-Id': '01399850',
        'X-Sys-Type': 'om'
    })
    # simulate_request.execute(test=True)
    simulate_request.execute(test=False)


if __name__ == '__main__':
    # ContextIms(), ContextEwms(), ContextOpcWeb(), ContextMscpOM()
    context = ContextIms()
    # db_use_local
    context.db_use_local()
    # request_use_local, request_use_prod
    context.request_use_prod()
    execute_request(context)
