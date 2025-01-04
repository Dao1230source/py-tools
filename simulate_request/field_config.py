# -*- coding:utf-8 -*-
import re

import numpy as np
import pandas as pd

URL = 'url'
IS_BATCH = 'is_batch'
BATCH_SIZE = 100
MAX_SIZE = 'max_size'
GROUP_FIELDS = 'group_fields'
# 包装参数
PARAM_PACK = "param_pack"
PARAM_PACK_FIELD = "param_pack_field"
FIELD_MAP = 'field_map'
PRIMARY_KEYS = 'primary_keys'
# field 默认值 None
FIELD_DEFAULT_NONE = '\\None'
RESULT_STATS_FUNC = 'result_stats_func'


class Field:
    def __init__(self, name, alias=None, default=None, format_func=None, merge_func=None):
        """
        请求参数的配置
        :param name: 参数名
        :param alias: 参数别名，如果通过name无法找到，再通过alias查找
        :param default: 默认值，
        1、可以是直接量
        2、也可以是另一个Field的值。此时应该注意先后顺序
        3、由于处理 default 时，需要通过 is not None来判断是否设置值，故使用 '\\None' 这个特殊值来表示None
        :param format_func: 字段值的格式化方法，方法参数是当前处理的Field的值
        :param merge_func: 该字段值和其他字段值合并操作，对当前列 Series 操作，参数是(Field, pd.DataFrame)
        """
        self.name = name
        if alias is not None:
            assert isinstance(alias, list)
            for a in alias:
                assert isinstance(a, Field)
        self.alias = alias
        if format_func is not None:
            assert callable(format_func)
        self.default = default
        self.format_func = format_func
        self.merge_func = merge_func


class RequestStats:
    def __init__(self):
        """
        统计http请求的输入输出
        total_num: 参数总条数
        success_num: 成功条数
        success_records: 执行成功的返回值
        fail_num: 失败条数
        fail_records: 执行失败的返回值
        """
        self.total_num = 0
        self.success_num = 0
        self.success_records = []
        self.fail_num = 0
        self.fail_records = []

    def success(self, res: any):
        self.success_records.append(res)
        self.success_num += 1

    def fail(self, res: any):
        self.fail_records.append(res)
        self.fail_num += 1


def data_update_field(data: pd.DataFrame, field: Field, exec_field_func=True) -> pd.Series:
    field_name = field.name
    # 如果field_name不存在，通过别名查找，并改名
    if field_name not in data.columns and field.alias is not None:
        for a in field.alias:
            value_after = data_update_field(data, a)
            if value_after is not None:
                data.rename(columns={a.name: field_name}, inplace=True)
                break
    if exec_field_func:
        # 对字段值进行一些额外操作
        if field.format_func is not None:
            data[field_name] = data[field_name].map(field.format_func)
        # 将本列字段和data中的其他字段值进行操作
        if field.merge_func is not None:
            data[field_name] = field.merge_func(field, data)
    # 设置默认值
    if field.default is not None:
        # 字段不存在，默认None
        if field_name not in data.columns:
            data[field_name] = None
        # 默认值是其他字段的值
        if isinstance(field.default, Field):
            data[field_name].fillna(data_update_field(data, field.default, False), inplace=True)
        # 默认值是直接量，str、int等
        elif field.default != FIELD_DEFAULT_NONE:
            # 但 default == '\\None' 这个特殊值时，不处理
            data.fillna({field_name: field.default}, inplace=True)
    return data[field_name] if field_name in data.columns else None


def demand_id_merge_func(self: Field, data: pd.DataFrame) -> pd.Series:
    """
    对当前列 Series 操作
    :param self: Field
    :param data: DataFrame
    :return: Series 当前列
    """
    field_name = self.name
    demand_id_val = data[field_name]
    # 如果有版本号这个字段，和需求ID拼接（等于1的除外）
    if 'demand_version' in data.columns:
        demand_version = data['demand_version']
        # 可能是np.nan的填充 1，可能是float类型转int，最后转str
        demand_version = demand_version.fillna(1).astype(np.int32).astype(str)
        # 版本号 == '1' 的不拼接，!= '1'的 和 demandId 拼接
        demand_version.where(demand_version == '1', '-' + demand_version, inplace=True)
        demand_version.where(demand_version != '1', inplace=True)
        demand_id_val = demand_id_val.str.cat(demand_version, na_rep='')
    return demand_id_val


def company_code_merge_func(self: Field, data: pd.DataFrame) -> pd.Series:
    """
    对当前列 Series 操作
    :param self: Field
    :param data: DataFrame
    :return: Series 当前列
    """
    field_name = self.name
    if field_name not in data.columns:
        data[field_name] = None

    if 'warehouseCode' in data.columns:
        rdc_warehouse = ['SCM001', 'SCM002', 'SCM003', 'SCM004', 'SCM005', 'SCM006', 'SCM007', 'SCM008', 'SCM009',
                         'SCM010']

        def set_company_code(row: pd.Series):
            if row['warehouseCode'] in rdc_warehouse:
                return 'C201'
            else:
                return 'SF'

        data[field_name] = data.apply(func=set_company_code, axis=1)
    return data[field_name]


def inventory_status_format_func(field_value: any):
    if field_value == '新品':
        return 10
    elif field_value == '旧品':
        return 20
    elif field_value == '旧品不可用':
        return 30
    else:
        return field_value


def order_pattern_format_func(field_value: any):
    if field_value == 'TOC':
        return 1
    elif field_value == 'TOB':
        return 2
    elif field_value == 'TO客户':
        return 3
    else:
        return field_value


def operate_cancel_batch_stats(param, result):
    """
    批量删除的结果统计
    :param param: param
    :param result:  result
    :return: RequestStats
    """
    stats = RequestStats()
    stats.total_num = len(param)
    resp = result['content']
    for r in resp:
        if 'remark1' in r and r['remark1'] is not None and 'code' in r['remark1'] \
                and '需求记录不存在' not in r['remark1']:
            stats.fail(r['remark1'])
        else:
            stats.success(r)
    return stats


def pullback_stats(param, result):
    """
    opc-web 批量拉回的结果统计
    :param param: param
    :param result:  result
    :return: RequestStats
    """
    stats = RequestStats()
    stats.total_num = len(param['content']['pullbackParams'])
    r = result['content']
    stats.success_num = r['successCount']
    stats.fail_num = r['failCount']
    for r in re.findall(r'\[[\w\-,"]+]+拉回成功！|\[[\w\-,"]+]+拉回失败[一-龥，！]+', r['msg']):
        if '拉回成功' in r:
            stats.success(r)
        else:
            stats.fail(r)
    return stats


def sync_inventory_data_stats(param, result):
    stats = RequestStats()
    stats.total_num = len(param)
    if result['success']:
        stats.success_num = len(param)
    else:
        stats.fail_records.append(result)
    return stats


pk_id = Field('id')
demand_id = Field('demand_id')
detail_id = Field('detail_id')
search_id = Field('search_id')
demand_id_cn = Field('需求单号')
demandId = Field('demandId', [demand_id, search_id, demand_id_cn], merge_func=demand_id_merge_func)
demandId_opc = Field('demandId', [demand_id, detail_id, demand_id_cn])
warehouse_code = Field('warehouse_code')
from_warehouse_code = Field('from_warehouse_code')
warehouse_code_cn = Field('仓库代码')
warehouseCode = Field('warehouseCode', alias=[from_warehouse_code, warehouse_code, warehouse_code_cn])
material_code_cn = Field('物料代码')
materielCode = Field('materielCode')
materialCode = Field('materialCode', alias=[material_code_cn, materielCode])
sku_no = Field('sku_no')
materiel_code = Field('materiel_code')
sku_no_cn = Field('物资编码')
skuNo = Field('skuNo', [sku_no, materiel_code, sku_no_cn, materialCode])
inventory_status = Field('inventory_status')
inventory_status_cn = Field('库存状态', format_func=inventory_status_format_func)
remark2 = Field('remark2')
inventoryStatus = Field('inventoryStatus', [inventory_status, remark2, inventory_status_cn], default="10")
company_code = Field('company_code')
companyCode = Field('companyCode', [company_code], merge_func=company_code_merge_func)
unlockDemandAllotLockKey = Field('unlockDemandAllotLockKey', default=False)
unlockGroupedDemandAllotLockKeys = Field('unlockGroupedDemandAllotLockKeys', default=False)
demand_num = Field('demand_num')
demandNum = Field('demandNum')
numbers = Field('numbers')
amount = Field('amount', [demand_num, demandNum, numbers])
plan_type = Field('plan_type', format_func=lambda x: x[-1])
planType = Field('type', [plan_type])
order_type = Field('order_type')
orderType = Field('orderType', [order_type])
deliver_address = Field('deliver_address')
deliverAddress = Field('deliverAddress', [deliver_address], default=FIELD_DEFAULT_NONE)
area_code = Field('area_code')
areaCode = Field('areaCode', [area_code])
policy_id = Field('policy_id')
policyId = Field('policyId', [policy_id], default="SF")
collect_id = Field('collect_id')
union_id = Field('union_id')
collectId_cn = Field('出库单号')
collectId = Field('collectId', [collect_id, union_id], default=demandId)
collectId_opc = Field('collectId', [collect_id, union_id, collectId_cn])
asn_id = Field('asn_id')
asnId = Field('asnId', [asn_id])
on_way_id = Field('on_way_id')
onWayId = Field('onWayId', [on_way_id], default=FIELD_DEFAULT_NONE)
unique_id = Field('unique_id')
uniqueId = Field('uniqueId', [unique_id])
cg_id = Field('cg_id')
cgId = Field('cgId', [cg_id])
availableQty = Field('availableQty')
availableGap = Field('availableGap')
availableMustPositiveOrZero = Field('availableMustPositiveOrZero', default=True)
totalMustPositiveOrZero = Field('totalMustPositiveOrZero', default=True)
stock_id = Field('stock_id')
stockId = Field('stockId', [stock_id])
_type = Field('type')
_status = Field('status')
freeze_id = Field('freeze_id')
freezeId = Field('freezeId', [freeze_id])
pull_reason = Field('pull_reason')
pullReason = Field('pullReason', [pull_reason], default="2022-09-01成都区封仓 180529（李皇华）")
locationCode_cn = Field('库位', default='L0')
locationCode = Field('locationCode', alias=[locationCode_cn], default='L0')
availableAmount = Field('availableAmount', default=0.0)
occupy_amount_cn = Field('占用库存')
occupyAmount = Field('occupyAmount', alias=[occupy_amount_cn], default=0.0)
on_way_amount_cn = Field('在途库存')
onWayAmount = Field('onWayAmount', alias=[on_way_amount_cn], default=0.0)
freeze_amount_cn = Field('冻结库存')
freezeAmount = Field('freezeAmount', alias=[freeze_amount_cn], default=0.0)
totalAmount_cn = Field('在库数量')
totalAmount = Field('totalAmount', alias=[totalAmount_cn], default=0.0)
key = Field('key')
hash_key = Field('hash_key')
hashKey = Field('hashHey', alias=[hash_key], default=FIELD_DEFAULT_NONE)
value = Field('value', default=FIELD_DEFAULT_NONE)
hash_value = Field('hash_value')
hashValue = Field('hashValue', alias=[hash_value], default=FIELD_DEFAULT_NONE)
arriveDate = Field('arriveDate')
carrier = Field('carrier')
month_card_cn = Field('月结卡号')
monthCard = Field('monthCard', alias=[month_card_cn])
order_pattern_cn = Field('订单模式')
orderPattern = Field('orderPattern', alias=[order_pattern_cn], format_func=order_pattern_format_func)
startTime = Field('startTime')
endTime = Field('endTime')
mapperName = Field('mapperName')
selectColumnName = Field('selectColumnName')
encryptColumnName = Field('encryptColumnName')
encryptFieldName = Field('encryptFieldName')
dataType = Field('dataType')
values = Field('values')
text = Field('text')
texts = Field('texts')
resultType = Field('resultType')
userId = Field('userId')
empCode_cn = Field('员工工号')
empCode = Field('empCode', alias=[empCode_cn])
supplyCode_cn = Field('物资编码')
supplyCode = Field('supplyCode', alias=[supplyCode_cn])
supplyProperty = Field('supplyProperty')
bizId = Field('bizId')
quantity_cn = Field('数量')
bizQuantity = Field('bizQuantity', alias=[quantity_cn])
bizScene = Field('bizScene')
confirmQuantity = Field('confirmQuantity')


def config_json():
    return {
        "inventorySummary": {
            URL: 'inventory/manage/inner/inventorySummary',
            IS_BATCH: False,
            FIELD_MAP: [warehouseCode, skuNo, inventoryStatus, companyCode]
        },
        "demandMatchBatch": {
            URL: 'inventory/manage/inner/demandMatchBatch',
            IS_BATCH: True,
            GROUP_FIELDS: ["collectId"],
            MAX_SIZE: 1000,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, planType, orderType,
                        deliverAddress, areaCode, policyId, collectId]
        },
        "demandMatchExecute": {
            URL: 'inventory/manage/inner/demandMatchExecute',
            IS_BATCH: False,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, planType, orderType,
                        deliverAddress, areaCode, policyId, collectId]
        },
        "inventoryUpdate": {
            URL: 'inventory/manage/inner/inventoryUpdate',
            IS_BATCH: False,
            FIELD_MAP: [warehouseCode, skuNo, inventoryStatus, companyCode, availableGap,
                        availableMustPositiveOrZero, totalMustPositiveOrZero]
        },
        "inventoryRefreshPoolBatch": {
            URL: 'inventory/manage/inner/inventoryRefreshPoolBatch',
            IS_BATCH: True,
            FIELD_MAP: [warehouseCode, skuNo, inventoryStatus, companyCode, unlockDemandAllotLockKey,
                        unlockGroupedDemandAllotLockKeys],
        },
        "demandOperateCancel": {
            URL: 'inventory/manage/inner/demandOperateCancel',
            IS_BATCH: False,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode],
        },
        "demandOperateCancelBatch": {
            URL: 'inventory/manage/inner/demandOperateCancelBatch',
            IS_BATCH: True,
            RESULT_STATS_FUNC: operate_cancel_batch_stats,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode],
        },
        "scheduleInventoryCheck": {
            URL: 'inventory/manage/inner/scheduleInventoryCheck',
            IS_BATCH: True,
            FIELD_MAP: [warehouseCode, skuNo, inventoryStatus, companyCode],
            PARAM_PACK: {"isSpecific": True, "isCompareGreaterVersion": False, "migrationPendingData": True,
                         "directUse": True, "isRefreshGroupCache": False, "checkFirst": False,
                         "inventoryUnitList": []},
            PARAM_PACK_FIELD: "inventoryUnitList"
        },
        "demandOperateFinish": {
            URL: 'inventory/manage/inner/demandOperateFinish',
            IS_BATCH: False,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode],
        },
        "demandOperateFinishBatch": {
            URL: 'inventory/manage/inner/demandOperateFinishBatch',
            IS_BATCH: True,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode],
        },
        "demandOperateDelivery": {
            URL: 'inventory/manage/inner/demandOperateDelivery',
            IS_BATCH: False,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode, amount],
        },
        "demandOperateDeliveryBatch": {
            URL: 'inventory/manage/inner/demandOperateDeliveryBatch',
            IS_BATCH: True,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode, amount]
        },
        "asnSync": {
            URL: 'inventory/manage/inner/asnSync',
            IS_BATCH: False,
            FIELD_MAP: [asnId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, onWayId, uniqueId],
        },
        "asnSyncBatch": {
            URL: 'inventory/manage/inner/asnSyncBatch',
            IS_BATCH: True,
            FIELD_MAP: [asnId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, onWayId, uniqueId],
        },
        "onWayDelBatch": {
            URL: 'inventory/manage/inner/onWayDelBatch',
            IS_BATCH: True,
            FIELD_MAP: [cgId, warehouseCode, skuNo, inventoryStatus, companyCode]
        },
        "scheduleBalanceExecute": {
            URL: 'inventory/manage/inner/scheduleBalanceExecute',
            IS_BATCH: True,
            FIELD_MAP: [warehouseCode, skuNo, inventoryStatus, companyCode],
            PARAM_PACK: {"inventoryUnitList": []},
            PARAM_PACK_FIELD: "inventoryUnitList"
        },
        "exceptionConfirm": {
            URL: 'inventory/manage/inner/exceptionConfirm',
            IS_BATCH: True,
            FIELD_MAP: [warehouseCode, skuNo, inventoryStatus, companyCode, availableQty, availableGap],
            PARAM_PACK: {},
            PARAM_PACK_FIELD: "content"
        },
        "stockApprove": {
            URL: 'inventory/manage/inner/stockApprove',
            IS_BATCH: False,
            FIELD_MAP: [stockId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, _type, uniqueId]
        },
        "stockReview": {
            URL: 'inventory/manage/inner/stockReview',
            IS_BATCH: False,
            FIELD_MAP: [stockId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, _status, uniqueId]
        },
        "inventoryFreeze": {
            URL: 'inventory/manage/inner/inventoryFreeze',
            IS_BATCH: False,
            FIELD_MAP: [freezeId, warehouseCode, skuNo, inventoryStatus, companyCode, amount, _type],
        },
        "analyseDemandIsEnough": {
            URL: 'inventory/manage/inner/analyseDemandIsEnough',
            IS_BATCH: False,
            FIELD_MAP: [demandId, warehouseCode, skuNo, inventoryStatus, companyCode],
        },
        "redisGet": {
            URL: 'inventory/manage/inner/redisGet',
            IS_BATCH: False,
            FIELD_MAP: [_type, key, value, hashKey, hashValue]
        },
        "redisSet": {
            URL: 'inventory/manage/inner/redisSet',
            IS_BATCH: False,
            FIELD_MAP: [_type, key, hashKey, value]
        },
        "groupSkuSelect": {
            URL: 'inventory/manage/inner/groupSkuSelect',
            IS_BATCH: True,
            FIELD_MAP: [skuNo]
        },

        "demand/batch/outWarehouse/pullback": {
            URL: 'api/web/demand/batch/outWarehouse/pullback',
            IS_BATCH: True,
            MAX_SIZE: 50,
            RESULT_STATS_FUNC: pullback_stats,
            FIELD_MAP: [demandId_opc, pullReason, orderType, collectId_opc],
            PARAM_PACK: {"content": {'pullbackParams': {}}},
            PARAM_PACK_FIELD: "pullbackParams"
        },
        "demand/outWarehouse/modify": {
            URL: 'api/web/demand/outWarehouse/modify',
            IS_BATCH: False,
            FIELD_MAP: [demandId, materielCode, demandNum, arriveDate, carrier, collectId_opc],
            PARAM_PACK: {"content": {}},
            PARAM_PACK_FIELD: "content"
        },
        "whcodeMonthcard/addWhcodeMonthcard": {
            URL: 'api/web/whcodeMonthcard/addWhcodeMonthcard',
            IS_BATCH: False,
            FIELD_MAP: [warehouseCode, monthCard, orderPattern],
            PARAM_PACK: {"content": {}},
            PARAM_PACK_FIELD: "content"
        },
        # ewms
        "syncInventoryData": {
            URL: 'app/inventory/syncInventoryData',
            IS_BATCH: True,
            RESULT_STATS_FUNC: sync_inventory_data_stats,
            FIELD_MAP: [warehouseCode, materialCode, inventoryStatus, locationCode, availableAmount, occupyAmount,
                        onWayAmount, freezeAmount, totalAmount]
        },
        # mscp-datasource
        "syncWarehouse": {
            URL: 'external-datasource-provider/manual/syncWarehouse',
            IS_BATCH: False,
            FIELD_MAP: [startTime]
        },
        "manualEncrypt": {
            URL: 'external-datasource-provider/manual/manualEncrypt',
            IS_BATCH: False,
            FIELD_MAP: [startTime, endTime, values, mapperName, selectColumnName,
                        encryptFieldName, encryptColumnName, dataType]
        },
        "encrypt": {
            URL: 'encryptor/encrypt',
            IS_BATCH: False,
            FIELD_MAP: [dataType, text]
        },
        "encryptBatch": {
            URL: 'encryptor/encryptBatch',
            IS_BATCH: False,
            FIELD_MAP: [dataType, texts]
        },
        "decryptBatchAsMap": {
            URL: 'encryptor/decryptBatchAsMap',
            IS_BATCH: False,
            FIELD_MAP: [dataType, texts, resultType, userId]
        },
        "inSubmit": {
            URL: 'onHand/inSubmit',
            IS_BATCH: True,
            FIELD_MAP: [empCode, supplyCode, supplyProperty, inventoryStatus, bizId, bizQuantity, bizScene]
        },
        "inConfirm": {
            URL: 'onHand/inConfirm',
            IS_BATCH: True,
            FIELD_MAP: [empCode, supplyCode, supplyProperty, inventoryStatus, bizId, bizQuantity, bizScene,
                        confirmQuantity]
        },
        "inSubmitAndConfirm": {
            URL: 'onHand/inSubmitAndConfirm',
            IS_BATCH: True,
            FIELD_MAP: [empCode, supplyCode, supplyProperty, inventoryStatus, bizId, bizQuantity, bizScene]
        }
    }


if __name__ == '__main__':
    pass
