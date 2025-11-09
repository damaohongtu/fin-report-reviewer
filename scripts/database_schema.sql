-- =====================================================
-- A股上市公司财务报表数据库结构
-- =====================================================
-- 说明：基于Wind数据结构设计
-- 适用：A股上市公司财务数据（沪、深、北证券交易所）
-- 生成时间：2024年
-- =====================================================

-- 创建Schema（可选）
-- CREATE SCHEMA IF NOT EXISTS financial_data;
-- SET search_path TO financial_data;

-- =====================================================
-- 1. A股资产负债表 (A-Share Balance Sheet)
-- =====================================================

CREATE TABLE IF NOT EXISTS a_share_balance_sheet (
    -- 主键字段
    stkcd VARCHAR(10) NOT NULL,                    -- 证券代码
    accper DATE NOT NULL,                          -- 统计截止日期
    typrep CHAR(1) NOT NULL,                       -- 报表类型：A=合并报表，B=母公司报表
    
    -- 基本信息
    short_name VARCHAR(100),                       -- 证券简称
    if_correct SMALLINT DEFAULT 0,                 -- 是否发生差错更正：0=否，1=是
    declare_date VARCHAR(200),                     -- 差错更正披露日期（多个日期用逗号分隔）
    
    -- 流动资产
    a001101000 NUMERIC(20, 2),                     -- 货币资金
    a0d1101101 NUMERIC(20, 2),                     -- 其中:客户资金存款
    a0d1102000 NUMERIC(20, 2),                     -- 结算备付金
    a0d1102101 NUMERIC(20, 2),                     -- 其中：客户备付金
    a0b1103000 NUMERIC(20, 2),                     -- 现金及存放中央银行款项
    a0b1104000 NUMERIC(20, 2),                     -- 存放同业款项
    a0b1105000 NUMERIC(20, 2),                     -- 贵金属
    a0f1106000 NUMERIC(20, 2),                     -- 拆出资金净额
    a001107000 NUMERIC(20, 2),                     -- 交易性金融资产
    a0f1108000 NUMERIC(20, 2),                     -- 衍生金融资产
    a001109000 NUMERIC(20, 2),                     -- 短期投资净额
    a001110000 NUMERIC(20, 2),                     -- 应收票据净额
    a001111000 NUMERIC(20, 2),                     -- 应收账款净额
    a001127000 NUMERIC(20, 2),                     -- 应收款项融资
    a001112000 NUMERIC(20, 2),                     -- 预付款项净额
    a0i1113000 NUMERIC(20, 2),                     -- 应收保费净额
    a0i1114000 NUMERIC(20, 2),                     -- 应收分保账款净额
    a0i1115000 NUMERIC(20, 2),                     -- 应收代位追偿款净额
    a0i1116000 NUMERIC(20, 2),                     -- 应收分保合同准备金净额
    a0i1116101 NUMERIC(20, 2),                     -- 其中:应收分保未到期责任准备金净额
    a0i1116201 NUMERIC(20, 2),                     -- 其中:应收分保未决赔款准备金净额
    a0i1116301 NUMERIC(20, 2),                     -- 其中:应收分保寿险责任准备金净额
    a0i1116401 NUMERIC(20, 2),                     -- 其中:应收分保长期健康险责任准备金净额
    a001119000 NUMERIC(20, 2),                     -- 应收利息净额
    a001120000 NUMERIC(20, 2),                     -- 应收股利净额
    a001121000 NUMERIC(20, 2),                     -- 其他应收款净额
    a0f1122000 NUMERIC(20, 2),                     -- 买入返售金融资产净额
    a001123000 NUMERIC(20, 2),                     -- 存货净额
    a001123101 NUMERIC(20, 2),                     -- 其中：数据资源（存货）
    a001128000 NUMERIC(20, 2),                     -- 合同资产
    a001129000 NUMERIC(20, 2),                     -- 持有待售资产
    a001124000 NUMERIC(20, 2),                     -- 一年内到期的非流动资产
    a0d1126000 NUMERIC(20, 2),                     -- 存出保证金
    a001125000 NUMERIC(20, 2),                     -- 其他流动资产
    a001100000 NUMERIC(20, 2),                     -- 流动资产合计
    
    -- 非流动资产
    a0i1224000 NUMERIC(20, 2),                     -- 保户质押贷款净额
    a0i1225000 NUMERIC(20, 2),                     -- 定期存款
    a0b1201000 NUMERIC(20, 2),                     -- 发放贷款及垫款净额
    a001226000 NUMERIC(20, 2),                     -- 债权投资
    a0f1132000 NUMERIC(20, 2),                     -- 以摊余成本计量的金融资产
    a001202000 NUMERIC(20, 2),                     -- 可供出售金融资产净额
    a001227000 NUMERIC(20, 2),                     -- 其他债权投资
    a0f1232000 NUMERIC(20, 2),                     -- 以公允价值计量且其变动计入其他综合收益的债务工具投资
    a001203000 NUMERIC(20, 2),                     -- 持有至到期投资净额
    a001204000 NUMERIC(20, 2),                     -- 长期应收款净额
    a001205000 NUMERIC(20, 2),                     -- 长期股权投资净额
    a001228000 NUMERIC(20, 2),                     -- 其他权益工具投资
    a0f1233000 NUMERIC(20, 2),                     -- 以公允价值计量且其变动计入其他综合收益的权益工具投资
    a0f1133000 NUMERIC(20, 2),                     -- 以公允价值计量且其变动计入其他综合收益的金融资产
    a001229000 NUMERIC(20, 2),                     -- 其他非流动金融资产
    a001206000 NUMERIC(20, 2),                     -- 长期债权投资净额
    a001207000 NUMERIC(20, 2),                     -- 长期投资净额
    a0i1209000 NUMERIC(20, 2),                     -- 存出资本保证金
    a0i1210000 NUMERIC(20, 2),                     -- 独立账户资产
    a001211000 NUMERIC(20, 2),                     -- 投资性房地产净额
    a001212000 NUMERIC(20, 2),                     -- 固定资产净额
    a001213000 NUMERIC(20, 2),                     -- 在建工程净额
    a001214000 NUMERIC(20, 2),                     -- 工程物资
    a001215000 NUMERIC(20, 2),                     -- 固定资产清理
    a001216000 NUMERIC(20, 2),                     -- 生产性生物资产净额
    a001217000 NUMERIC(20, 2),                     -- 油气资产净额
    a001230000 NUMERIC(20, 2),                     -- 使用权资产
    a001218000 NUMERIC(20, 2),                     -- 无形资产净额
    a0d1218101 NUMERIC(20, 2),                     -- 其中:交易席位费
    a001218201 NUMERIC(20, 2),                     -- 其中：数据资源（无形资产）
    a001219000 NUMERIC(20, 2),                     -- 开发支出
    a001219101 NUMERIC(20, 2),                     -- 其中：数据资源（开发支出）
    a001220000 NUMERIC(20, 2),                     -- 商誉净额
    a001221000 NUMERIC(20, 2),                     -- 长期待摊费用
    a001222000 NUMERIC(20, 2),                     -- 递延所得税资产
    a0f1224000 NUMERIC(20, 2),                     -- 代理业务资产
    a001223000 NUMERIC(20, 2),                     -- 其他非流动资产
    a001200000 NUMERIC(20, 2),                     -- 非流动资产合计
    a0f1300000 NUMERIC(20, 2),                     -- 其他资产
    a001000000 NUMERIC(20, 2),                     -- 资产总计
    
    -- 流动负债
    a002101000 NUMERIC(20, 2),                     -- 短期借款
    a0d2101101 NUMERIC(20, 2),                     -- 其中:质押借款
    a0d2130000 NUMERIC(20, 2),                     -- 应付短期融资款
    a0b2102000 NUMERIC(20, 2),                     -- 向中央银行借款
    a0b2103000 NUMERIC(20, 2),                     -- 吸收存款及同业存放
    a0b2103101 NUMERIC(20, 2),                     -- 其中：同业及其他金融机构存放款项
    a0b2103201 NUMERIC(20, 2),                     -- 其中：吸收存款
    a0f2104000 NUMERIC(20, 2),                     -- 拆入资金
    a002105000 NUMERIC(20, 2),                     -- 交易性金融负债
    a0f2106000 NUMERIC(20, 2),                     -- 衍生金融负债
    a002107000 NUMERIC(20, 2),                     -- 应付票据
    a002108000 NUMERIC(20, 2),                     -- 应付账款
    a002109000 NUMERIC(20, 2),                     -- 预收款项
    a002128000 NUMERIC(20, 2),                     -- 合同负债
    a0f2110000 NUMERIC(20, 2),                     -- 卖出回购金融资产款
    a0i2111000 NUMERIC(20, 2),                     -- 应付手续费及佣金
    a002112000 NUMERIC(20, 2),                     -- 应付职工薪酬
    a002113000 NUMERIC(20, 2),                     -- 应交税费
    a002114000 NUMERIC(20, 2),                     -- 应付利息
    a002115000 NUMERIC(20, 2),                     -- 应付股利
    a0i2116000 NUMERIC(20, 2),                     -- 应付赔付款
    a0i2117000 NUMERIC(20, 2),                     -- 应付保单红利
    a0i2118000 NUMERIC(20, 2),                     -- 保户储金及投资款
    a0i2119000 NUMERIC(20, 2),                     -- 保险合同准备金
    a0i2119101 NUMERIC(20, 2),                     -- 其中:未到期责任准备金
    a0i2119201 NUMERIC(20, 2),                     -- 其中:未决赔款准备金
    a0i2119301 NUMERIC(20, 2),                     -- 其中:寿险责任准备金
    a0i2119401 NUMERIC(20, 2),                     -- 其中:长期健康险责任准备金
    a002120000 NUMERIC(20, 2),                     -- 其他应付款
    a0i2121000 NUMERIC(20, 2),                     -- 应付分保账款
    a0d2122000 NUMERIC(20, 2),                     -- 代理买卖证券款
    a0d2123000 NUMERIC(20, 2),                     -- 代理承销证券款
    a0i2124000 NUMERIC(20, 2),                     -- 预收保费
    a002129000 NUMERIC(20, 2),                     -- 持有待售负债
    a002125000 NUMERIC(20, 2),                     -- 一年内到期的非流动负债
    a002126000 NUMERIC(20, 2),                     -- 其他流动负债
    a002127000 NUMERIC(20, 2),                     -- 递延收益-流动负债
    a002100000 NUMERIC(20, 2),                     -- 流动负债合计
    
    -- 非流动负债
    a002201000 NUMERIC(20, 2),                     -- 长期借款
    a0d2202000 NUMERIC(20, 2),                     -- 独立账户负债
    a002203000 NUMERIC(20, 2),                     -- 应付债券
    a002211000 NUMERIC(20, 2),                     -- 租赁负债
    a002204000 NUMERIC(20, 2),                     -- 长期应付款
    a002212000 NUMERIC(20, 2),                     -- 长期应付职工薪酬
    a002205000 NUMERIC(20, 2),                     -- 专项应付款
    a002206000 NUMERIC(20, 2),                     -- 长期负债合计
    a002207000 NUMERIC(20, 2),                     -- 预计负债
    a0f2210000 NUMERIC(20, 2),                     -- 代理业务负债
    a002208000 NUMERIC(20, 2),                     -- 递延所得税负债
    a002209000 NUMERIC(20, 2),                     -- 其他非流动负债
    a002210000 NUMERIC(20, 2),                     -- 递延收益-非流动负债
    a002200000 NUMERIC(20, 2),                     -- 非流动负债合计
    a0f2300000 NUMERIC(20, 2),                     -- 其他负债
    a002000000 NUMERIC(20, 2),                     -- 负债合计
    
    -- 所有者权益
    a003101000 NUMERIC(20, 2),                     -- 实收资本(或股本)
    a003112000 NUMERIC(20, 2),                     -- 其他权益工具
    a003112101 NUMERIC(20, 2),                     -- 其中：优先股
    a003112201 NUMERIC(20, 2),                     -- 其中：永续债
    a003112301 NUMERIC(20, 2),                     -- 其中：其他
    a003102000 NUMERIC(20, 2),                     -- 资本公积
    a003102101 NUMERIC(20, 2),                     -- 减：库存股
    a003103000 NUMERIC(20, 2),                     -- 盈余公积
    a0f3104000 NUMERIC(20, 2),                     -- 一般风险准备
    a003105000 NUMERIC(20, 2),                     -- 未分配利润
    a003106000 NUMERIC(20, 2),                     -- 外币报表折算差额
    a003107000 NUMERIC(20, 2),                     -- 加：未确认的投资损失
    a0f3108000 NUMERIC(20, 2),                     -- 交易风险准备
    a0f3109000 NUMERIC(20, 2),                     -- 专项储备
    a003111000 NUMERIC(20, 2),                     -- 其他综合收益
    a003100000 NUMERIC(20, 2),                     -- 归属于母公司所有者权益合计
    a003200000 NUMERIC(20, 2),                     -- 少数股东权益
    a003000000 NUMERIC(20, 2),                     -- 所有者权益合计
    a004000000 NUMERIC(20, 2),                     -- 负债与所有者权益总计
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (stkcd, accper, typrep)
);

-- 创建索引
CREATE INDEX idx_a_share_balance_sheet_stkcd ON a_share_balance_sheet(stkcd);
CREATE INDEX idx_a_share_balance_sheet_accper ON a_share_balance_sheet(accper);
CREATE INDEX idx_a_share_balance_sheet_short_name ON a_share_balance_sheet(short_name);

-- 表和字段注释
COMMENT ON TABLE a_share_balance_sheet IS 'A股上市公司资产负债表（沪深北交易所）';

-- 主键和基本字段
COMMENT ON COLUMN a_share_balance_sheet.stkcd IS '证券代码 - 以沪、深、北证券交易所公布的证券代码为准';
COMMENT ON COLUMN a_share_balance_sheet.accper IS '统计截止日期 - YYYY-MM-DD格式，前四位表示会计报表公布年度';
COMMENT ON COLUMN a_share_balance_sheet.typrep IS '报表类型 - A=合并报表，B=母公司报表';
COMMENT ON COLUMN a_share_balance_sheet.short_name IS '证券简称 - 以沪、深、北证券交易所公布的证券简称为准';
COMMENT ON COLUMN a_share_balance_sheet.if_correct IS '是否发生差错更正 - 0=否，1=是';
COMMENT ON COLUMN a_share_balance_sheet.declare_date IS '差错更正披露日期 - 多个日期用逗号分隔';

-- 流动资产
COMMENT ON COLUMN a_share_balance_sheet.a001101000 IS '货币资金 - 库存现金、银行结算户存款、外埠存款等的合计数';
COMMENT ON COLUMN a_share_balance_sheet.a0d1101101 IS '其中:客户资金存款 - 金融企业的客户资金存款数';
COMMENT ON COLUMN a_share_balance_sheet.a0d1102000 IS '结算备付金 - 证券业务的资金清算与交收而存入指定清算代理机构的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0d1102101 IS '其中：客户备付金 - 证券经纪业务取得的客户备付金';
COMMENT ON COLUMN a_share_balance_sheet.a0b1103000 IS '现金及存放中央银行款项 - 企业持有的现金、存放中央银行款项等总额';
COMMENT ON COLUMN a_share_balance_sheet.a0b1104000 IS '存放同业款项 - 企业（银行）存放于境内、境外银行和非银行金融机构的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0b1105000 IS '贵金属 - 企业（金融）持有的黄金、白银等贵金属存货的成本';
COMMENT ON COLUMN a_share_balance_sheet.a0f1106000 IS '拆出资金净额 - 拆借给境内、境外其他金融机构的款项与相关贷款损失准备之差额';
COMMENT ON COLUMN a_share_balance_sheet.a001107000 IS '交易性金融资产 - 为交易目的所持有的债券、股票、基金等金融资产的公允价值';
COMMENT ON COLUMN a_share_balance_sheet.a0f1108000 IS '衍生金融资产 - 企业持有的衍生工具、套期工具等属于衍生金融资产的金额';
COMMENT ON COLUMN a_share_balance_sheet.a001109000 IS '短期投资净额 - 能随时变现且持有时间不超过一年的股票和债券（2007年前）';
COMMENT ON COLUMN a_share_balance_sheet.a001110000 IS '应收票据净额 - 收到的未到期未向银行贴现的商业承兑汇票和银行承兑汇票';
COMMENT ON COLUMN a_share_balance_sheet.a001111000 IS '应收账款净额 - 因销售商品、提供劳务等业务应向购买单位收取的款项';
COMMENT ON COLUMN a_share_balance_sheet.a001127000 IS '应收款项融资 - 应收款项出售给银行或金融机构但具有追索权的融资';
COMMENT ON COLUMN a_share_balance_sheet.a001112000 IS '预付款项净额 - 按照购货合同规定预付给供应单位的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0i1113000 IS '应收保费净额 - 金融企业应向投保人收取但尚未收到的保费';
COMMENT ON COLUMN a_share_balance_sheet.a0i1114000 IS '应收分保账款净额 - 企业（保险）从事再保险业务应收取的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0i1115000 IS '应收代位追偿款净额 - 保险人承担赔偿责任后向第三者责任人索赔应取得的赔款';
COMMENT ON COLUMN a_share_balance_sheet.a0i1116000 IS '应收分保合同准备金净额 - 从事再保险业务确认的应收分保准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0i1116101 IS '其中:应收分保未到期责任准备金净额 - 分出的未赚保费，对当期分出保费的调整';
COMMENT ON COLUMN a_share_balance_sheet.a0i1116201 IS '其中:应收分保未决赔款准备金净额 - 应向再保险接受人摊回的应收分保未决赔款准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0i1116301 IS '其中:应收分保寿险责任准备金净额 - 应向再保险接受人摊回的应收分保寿险责任准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0i1116401 IS '其中:应收分保长期健康险责任准备金净额 - 应向再保险接受人摊回的长期健康险责任准备金';
COMMENT ON COLUMN a_share_balance_sheet.a001119000 IS '应收利息净额 - 因债权投资而应收取的利息';
COMMENT ON COLUMN a_share_balance_sheet.a001120000 IS '应收股利净额 - 因股权投资而应收取的现金股利';
COMMENT ON COLUMN a_share_balance_sheet.a001121000 IS '其他应收款净额 - 除应收票据、应收账款等以外的其他各种应收及暂付款项';
COMMENT ON COLUMN a_share_balance_sheet.a0f1122000 IS '买入返售金融资产净额 - 按返售协议先买入再按固定价格返售的金融资产所融出的资金';
COMMENT ON COLUMN a_share_balance_sheet.a001123000 IS '存货净额 - 持有以备出售的产成品或商品、在产品、原材料等';
COMMENT ON COLUMN a_share_balance_sheet.a001123101 IS '其中：数据资源（存货） - 确认为存货的数据资源的期末账面价值（2024年起）';
COMMENT ON COLUMN a_share_balance_sheet.a001128000 IS '合同资产 - 已向客户转让商品而有权收取对价的权利';
COMMENT ON COLUMN a_share_balance_sheet.a001129000 IS '持有待售资产 - 持有待售的非流动资产或处置组';
COMMENT ON COLUMN a_share_balance_sheet.a001124000 IS '一年内到期的非流动资产 - 一年内到期的非流动资产的账面价值';
COMMENT ON COLUMN a_share_balance_sheet.a0d1126000 IS '存出保证金 - 企业（金融）因办理业务需要存出或交纳的各种保证金';
COMMENT ON COLUMN a_share_balance_sheet.a001125000 IS '其他流动资产 - 不能列入流动资产其他各项目的流动资产';
COMMENT ON COLUMN a_share_balance_sheet.a001100000 IS '流动资产合计 - 流动资产各项目之合计';

-- 非流动资产
COMMENT ON COLUMN a_share_balance_sheet.a0i1224000 IS '保户质押贷款净额 - 保险企业发放的保户质押贷款扣除损失准备';
COMMENT ON COLUMN a_share_balance_sheet.a0i1225000 IS '定期存款 - 保险公司存放在金融机构的定期存款';
COMMENT ON COLUMN a_share_balance_sheet.a0b1201000 IS '发放贷款及垫款净额 - 企业发放的贷款和贴现资产扣减贷款损失准备';
COMMENT ON COLUMN a_share_balance_sheet.a001226000 IS '债权投资 - 债券购买人以购买债券形式投放资本（2019年起）';
COMMENT ON COLUMN a_share_balance_sheet.a0f1132000 IS '以摊余成本计量的金融资产 - 按摊余成本计量的金融资产';
COMMENT ON COLUMN a_share_balance_sheet.a001202000 IS '可供出售金融资产净额 - 可供出售的股票投资、债券投资等（2007年起）';
COMMENT ON COLUMN a_share_balance_sheet.a001227000 IS '其他债权投资 - 除债券以外的其他债权投资（2019年起）';
COMMENT ON COLUMN a_share_balance_sheet.a0f1232000 IS '以公允价值计量且其变动计入其他综合收益的债务工具投资 - FVOCI债务工具投资';
COMMENT ON COLUMN a_share_balance_sheet.a001203000 IS '持有至到期投资净额 - 到期日固定、回收金额固定且有意图和能力持有至到期的非衍生金融资产';
COMMENT ON COLUMN a_share_balance_sheet.a001204000 IS '长期应收款净额 - 融资租赁、递延方式销售等产生的长期应收款项';
COMMENT ON COLUMN a_share_balance_sheet.a001205000 IS '长期股权投资净额 - 对子公司、联营企业和合营企业的长期股权投资';
COMMENT ON COLUMN a_share_balance_sheet.a001228000 IS '其他权益工具投资 - 指定为FVOCI的非交易性权益工具投资（2018年起）';
COMMENT ON COLUMN a_share_balance_sheet.a0f1233000 IS '以公允价值计量且其变动计入其他综合收益的权益工具投资 - FVOCI权益工具投资';
COMMENT ON COLUMN a_share_balance_sheet.a0f1133000 IS '以公允价值计量且其变动计入其他综合收益的金融资产 - FVOCI金融资产';
COMMENT ON COLUMN a_share_balance_sheet.a001229000 IS '其他非流动金融资产 - 其他非流动金融资产（2019年起）';
COMMENT ON COLUMN a_share_balance_sheet.a001206000 IS '长期债权投资净额 - 不准备在一年内变现的各种债权性质的投资（2007年前）';
COMMENT ON COLUMN a_share_balance_sheet.a001207000 IS '长期投资净额 - 长期股权投资、长期债券投资与其他长期投资合计（2007年前）';
COMMENT ON COLUMN a_share_balance_sheet.a0i1209000 IS '存出资本保证金 - 企业（保险）按规定比例缴存的资本保证金';
COMMENT ON COLUMN a_share_balance_sheet.a0i1210000 IS '独立账户资产 - 企业（保险）对投资连结产品确认的独立账户资产价值';
COMMENT ON COLUMN a_share_balance_sheet.a001211000 IS '投资性房地产净额 - 为赚取租金或资本增值而持有的房地产';
COMMENT ON COLUMN a_share_balance_sheet.a001212000 IS '固定资产净额 - 固定资产原价扣除累计折旧和减值准备后的净额';
COMMENT ON COLUMN a_share_balance_sheet.a001213000 IS '在建工程净额 - 各项未完工程的实际支出扣除减值准备后的净额';
COMMENT ON COLUMN a_share_balance_sheet.a001214000 IS '工程物资 - 各项工程尚未使用的工程物资的实际成本';
COMMENT ON COLUMN a_share_balance_sheet.a001215000 IS '固定资产清理 - 因出售、毁损、报废等原因转入清理但尚未清理完毕的固定资产';
COMMENT ON COLUMN a_share_balance_sheet.a001216000 IS '生产性生物资产净额 - 为产出农产品、提供劳务或出租等目的持有的生物资产';
COMMENT ON COLUMN a_share_balance_sheet.a001217000 IS '油气资产净额 - 企业（石油天然气开采）持有的矿区权益和油气井资产';
COMMENT ON COLUMN a_share_balance_sheet.a001230000 IS '使用权资产 - 承租人可在租赁期内使用租赁资产的权利（2019年起）';
COMMENT ON COLUMN a_share_balance_sheet.a001218000 IS '无形资产净额 - 专利权、商标权、著作权、土地使用权等扣除摊销和减值后的净额';
COMMENT ON COLUMN a_share_balance_sheet.a0d1218101 IS '其中:交易席位费 - 证券公司交纳的交易席位费的可回收金额';
COMMENT ON COLUMN a_share_balance_sheet.a001218201 IS '其中：数据资源（无形资产） - 确认为无形资产的数据资源账面价值（2024年起）';
COMMENT ON COLUMN a_share_balance_sheet.a001219000 IS '开发支出 - 开发过程中资本化后但还没有结转为无形资产的部分';
COMMENT ON COLUMN a_share_balance_sheet.a001219101 IS '其中：数据资源（开发支出） - 数据资源研发项目满足资本化条件的支出（2024年起）';
COMMENT ON COLUMN a_share_balance_sheet.a001220000 IS '商誉净额 - 企业合并中形成的商誉价值扣除减值准备后的净额';
COMMENT ON COLUMN a_share_balance_sheet.a001221000 IS '长期待摊费用 - 摊销期限在一年以上的各种费用';
COMMENT ON COLUMN a_share_balance_sheet.a001222000 IS '递延所得税资产 - 可抵扣暂时性差异产生的递延所得税资产';
COMMENT ON COLUMN a_share_balance_sheet.a0f1224000 IS '代理业务资产 - 不承担风险的代理业务形成的资产';
COMMENT ON COLUMN a_share_balance_sheet.a001223000 IS '其他非流动资产 - 除上述非流动资产以外的非流动资产合计';
COMMENT ON COLUMN a_share_balance_sheet.a001200000 IS '非流动资产合计 - 所有非流动资产的合计数';
COMMENT ON COLUMN a_share_balance_sheet.a0f1300000 IS '其他资产 - 金融企业披露的其他资产';
COMMENT ON COLUMN a_share_balance_sheet.a001000000 IS '资产总计 - 流动资产和非流动资产之合计';

-- 流动负债
COMMENT ON COLUMN a_share_balance_sheet.a002101000 IS '短期借款 - 借入的尚未归还的一年期以下（含一年）的借款';
COMMENT ON COLUMN a_share_balance_sheet.a0d2101101 IS '其中:质押借款 - 证券公司通过质押方式从银行融资获得的金额';
COMMENT ON COLUMN a_share_balance_sheet.a0d2130000 IS '应付短期融资款 - 企业应付的短期融资款项';
COMMENT ON COLUMN a_share_balance_sheet.a0b2102000 IS '向中央银行借款 - 银行向中央银行借入的临时周转借款等';
COMMENT ON COLUMN a_share_balance_sheet.a0b2103000 IS '吸收存款及同业存放 - 银行吸收的客户存款或其他金融机构存放的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0b2103101 IS '其中：同业及其他金融机构存放款项 - 其他银行或金融机构存入的清算款项';
COMMENT ON COLUMN a_share_balance_sheet.a0b2103201 IS '其中：吸收存款 - 企业（银行）吸收的除同业存放款项以外的其他存款';
COMMENT ON COLUMN a_share_balance_sheet.a0f2104000 IS '拆入资金 - 金融企业从金融机构拆入的款项';
COMMENT ON COLUMN a_share_balance_sheet.a002105000 IS '交易性金融负债 - 承担的交易性金融负债的公允价值';
COMMENT ON COLUMN a_share_balance_sheet.a0f2106000 IS '衍生金融负债 - 持有的衍生工具等属于衍生金融负债的金额';
COMMENT ON COLUMN a_share_balance_sheet.a002107000 IS '应付票据 - 为抵付货款等而开出的尚未到期付款的应付票据';
COMMENT ON COLUMN a_share_balance_sheet.a002108000 IS '应付账款 - 购买原材料、商品或接受劳务供应等应付给供应单位的款项';
COMMENT ON COLUMN a_share_balance_sheet.a002109000 IS '预收款项 - 按照购货合同规定预收购买单位的款项';
COMMENT ON COLUMN a_share_balance_sheet.a002128000 IS '合同负债 - 已收或应收客户对价而应向客户转让商品的义务（2018年起）';
COMMENT ON COLUMN a_share_balance_sheet.a0f2110000 IS '卖出回购金融资产款 - 按回购协议先卖出再按固定价格买入金融资产所融入的资金';
COMMENT ON COLUMN a_share_balance_sheet.a0i2111000 IS '应付手续费及佣金 - 保险企业因业务往来应支付的手续费及佣金';
COMMENT ON COLUMN a_share_balance_sheet.a002112000 IS '应付职工薪酬 - 根据规定应付给职工的各种薪酬';
COMMENT ON COLUMN a_share_balance_sheet.a002113000 IS '应交税费 - 按税法规定计算应交纳的各种税费';
COMMENT ON COLUMN a_share_balance_sheet.a002114000 IS '应付利息 - 按期计提的长期借款、应付债券等的利息';
COMMENT ON COLUMN a_share_balance_sheet.a002115000 IS '应付股利 - 经董事会或股东大会决议确定分配的、尚未支付的现金股利';
COMMENT ON COLUMN a_share_balance_sheet.a0i2116000 IS '应付赔付款 - 保险企业应支付但尚未支付的赔付款项';
COMMENT ON COLUMN a_share_balance_sheet.a0i2117000 IS '应付保单红利 - 企业（保险）按合同约定应付未付投保人的红利';
COMMENT ON COLUMN a_share_balance_sheet.a0i2118000 IS '保户储金及投资款 - 企业（保险）收到投保人的储金及投资型保险业务的投资款';
COMMENT ON COLUMN a_share_balance_sheet.a0i2119000 IS '保险合同准备金 - 包括未到期责任准备金、未决赔款准备金等';
COMMENT ON COLUMN a_share_balance_sheet.a0i2119101 IS '其中:未到期责任准备金 - 为尚未终止的非寿险保险责任提取的准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0i2119201 IS '其中:未决赔款准备金 - 为非寿险保险事故已发生尚未结案的赔案提取的准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0i2119301 IS '其中:寿险责任准备金 - 为尚未终止的人寿保险责任提取的准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0i2119401 IS '其中:长期健康险责任准备金 - 为尚未终止的长期健康保险责任提取的准备金';
COMMENT ON COLUMN a_share_balance_sheet.a002120000 IS '其他应付款 - 除应付票据、应付账款等以外的其他各项应付、暂收的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0i2121000 IS '应付分保账款 - 企业（保险）从事再保险业务应付未付的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0d2122000 IS '代理买卖证券款 - 企业（证券）代理客户买卖证券而收到的款项';
COMMENT ON COLUMN a_share_balance_sheet.a0d2123000 IS '代理承销证券款 - 企业（金融）采用承购包销或代销方式承销证券的应付资金';
COMMENT ON COLUMN a_share_balance_sheet.a0i2124000 IS '预收保费 - 企业（保险）收到未满足保费收入确认条件的保险费';
COMMENT ON COLUMN a_share_balance_sheet.a002129000 IS '持有待售负债 - 持有待售的处置组中的负债';
COMMENT ON COLUMN a_share_balance_sheet.a002125000 IS '一年内到期的非流动负债 - 一年内到期的非流动负债的账面价值';
COMMENT ON COLUMN a_share_balance_sheet.a002126000 IS '其他流动负债 - 不能列入流动负债其他各项目的流动负债';
COMMENT ON COLUMN a_share_balance_sheet.a002127000 IS '递延收益-流动负债 - 尚待确认的收入或收益（流动部分，2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a002100000 IS '流动负债合计 - 流动负债各项目之合计';

-- 非流动负债
COMMENT ON COLUMN a_share_balance_sheet.a002201000 IS '长期借款 - 向银行或其他金融机构借入的期限在一年期以上的各项借款';
COMMENT ON COLUMN a_share_balance_sheet.a0d2202000 IS '独立账户负债 - 企业（保险）对投资连结产品确认的独立账户负债';
COMMENT ON COLUMN a_share_balance_sheet.a002203000 IS '应付债券 - 为筹集长期资金而发行债券的本金和利息';
COMMENT ON COLUMN a_share_balance_sheet.a002211000 IS '租赁负债 - 尚未支付的租赁付款额的现值（2019年起）';
COMMENT ON COLUMN a_share_balance_sheet.a002204000 IS '长期应付款 - 除长期借款和应付债券以外的其他各种长期应付款';
COMMENT ON COLUMN a_share_balance_sheet.a002212000 IS '长期应付职工薪酬 - 长期应付职工薪酬';
COMMENT ON COLUMN a_share_balance_sheet.a002205000 IS '专项应付款 - 因承担专项建设任务等形成的应付款项';
COMMENT ON COLUMN a_share_balance_sheet.a002206000 IS '长期负债合计 - 长期借款+独立账户负债+应付债券+租赁负债+长期应付款+专项应付款';
COMMENT ON COLUMN a_share_balance_sheet.a002207000 IS '预计负债 - 预计的各项或有负债，如预计的待决诉讼费用';
COMMENT ON COLUMN a_share_balance_sheet.a0f2210000 IS '代理业务负债 - 不承担风险的代理业务收到的款项';
COMMENT ON COLUMN a_share_balance_sheet.a002208000 IS '递延所得税负债 - 应纳税暂时性差异产生的所得税负债';
COMMENT ON COLUMN a_share_balance_sheet.a002209000 IS '其他非流动负债 - 除上述非流动负债以外的非流动负债的合计';
COMMENT ON COLUMN a_share_balance_sheet.a002210000 IS '递延收益-非流动负债 - 尚待确认的收入或收益（非流动部分，2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a002200000 IS '非流动负债合计 - 所有非流动负债的合计';
COMMENT ON COLUMN a_share_balance_sheet.a0f2300000 IS '其他负债 - 金融企业披露的其他负债';
COMMENT ON COLUMN a_share_balance_sheet.a002000000 IS '负债合计 - 流动负债和非流动负债之合计';

-- 所有者权益
COMMENT ON COLUMN a_share_balance_sheet.a003101000 IS '实收资本(或股本) - 按公司章程规定，股东投入公司的股本总额';
COMMENT ON COLUMN a_share_balance_sheet.a003112000 IS '其他权益工具 - 除普通股以外归类为权益工具的金融工具（2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a003112101 IS '其中：优先股 - 在利润分红及剩余财产分配上优先于普通股（2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a003112201 IS '其中：永续债 - 不规定到期期限，持有人不能要求清偿本金但按期取得利息（2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a003112301 IS '其中：其他 - 其他不能归类到其他权益工具的内容（2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a003102000 IS '资本公积 - 包括股本溢价、法定财产重估增值、接受捐赠等';
COMMENT ON COLUMN a_share_balance_sheet.a003102101 IS '减：库存股 - 企业收购、转让或注销的本公司股份金额';
COMMENT ON COLUMN a_share_balance_sheet.a003103000 IS '盈余公积 - 按国家规定从利润中提取的公积金';
COMMENT ON COLUMN a_share_balance_sheet.a0f3104000 IS '一般风险准备 - 企业（金融）按规定从净利润中提取的一般风险准备';
COMMENT ON COLUMN a_share_balance_sheet.a003105000 IS '未分配利润 - 公司尚未分配的利润';
COMMENT ON COLUMN a_share_balance_sheet.a003106000 IS '外币报表折算差额 - 因记账本位币不同而产生的货币折算差额';
COMMENT ON COLUMN a_share_balance_sheet.a003107000 IS '加：未确认的投资损失 - 按权益法核算的长期投资项目，被投资企业负所有者权益之份额（2007年前）';
COMMENT ON COLUMN a_share_balance_sheet.a0f3108000 IS '交易风险准备 - 证券公司从税后利润中提取的交易风险准备金';
COMMENT ON COLUMN a_share_balance_sheet.a0f3109000 IS '专项储备 - 高危行业企业按规定提取的安全生产费等';
COMMENT ON COLUMN a_share_balance_sheet.a003111000 IS '其他综合收益 - 根据企业会计准则规定未在损益中确认的各项利得和损失扣除所得税后的净额（2015年起）';
COMMENT ON COLUMN a_share_balance_sheet.a003100000 IS '归属于母公司所有者权益合计 - 合并报表中归属于母公司所有者份额的权益';
COMMENT ON COLUMN a_share_balance_sheet.a003200000 IS '少数股东权益 - 子公司所有者权益中由母公司以外的其他投资者拥有的份额';
COMMENT ON COLUMN a_share_balance_sheet.a003000000 IS '所有者权益合计 - 股东权益各项目之合计';
COMMENT ON COLUMN a_share_balance_sheet.a004000000 IS '负债与所有者权益总计 - 负债与所有者权益各项目之总计，应等于资产总计';

-- 审计字段
COMMENT ON COLUMN a_share_balance_sheet.created_at IS '记录创建时间';
COMMENT ON COLUMN a_share_balance_sheet.updated_at IS '记录更新时间';

-- =====================================================
-- 2. A股利润表 (A-Share Income Statement)
-- =====================================================

CREATE TABLE IF NOT EXISTS a_share_income_statement (
    -- 主键字段
    stkcd VARCHAR(10) NOT NULL,                    -- 证券代码
    accper DATE NOT NULL,                          -- 统计截止日期
    typrep CHAR(1) NOT NULL,                       -- 报表类型：A=合并报表，B=母公司报表
    
    -- 基本信息
    short_name VARCHAR(100),                       -- 证券简称
    if_correct SMALLINT DEFAULT 0,                 -- 是否发生差错更正：0=否，1=是
    declare_date VARCHAR(200),                     -- 差错更正披露日期
    
    -- 营业收入
    b001100000 NUMERIC(20, 2),                     -- 营业总收入
    b001101000 NUMERIC(20, 2),                     -- 营业收入
    bbd1102000 NUMERIC(20, 2),                     -- 利息净收入
    bbd1102101 NUMERIC(20, 2),                     -- 利息收入
    bbd1102203 NUMERIC(20, 2),                     -- 利息支出
    b0i1103000 NUMERIC(20, 2),                     -- 已赚保费
    b0i1103101 NUMERIC(20, 2),                     -- 保险业务收入
    b0i1103111 NUMERIC(20, 2),                     -- 其中：分保费收入
    b0i1103203 NUMERIC(20, 2),                     -- 减：分出保费
    b0i1103303 NUMERIC(20, 2),                     -- 减：提取未到期责任准备金
    b0d1104000 NUMERIC(20, 2),                     -- 手续费及佣金净收入
    b0d1104101 NUMERIC(20, 2),                     -- 其中：代理买卖证券业务净收入
    b0d1104201 NUMERIC(20, 2),                     -- 其中:证券承销业务净收入
    b0d1104301 NUMERIC(20, 2),                     -- 其中：受托客户资产管理业务净收入
    b0d1104401 NUMERIC(20, 2),                     -- 手续费及佣金收入
    b0d1104501 NUMERIC(20, 2),                     -- 手续费及佣金支出
    b0f1105000 NUMERIC(20, 2),                     -- 其他业务收入
    
    -- 营业成本
    b001200000 NUMERIC(20, 2),                     -- 营业总成本
    b001201000 NUMERIC(20, 2),                     -- 营业成本
    b0i1202000 NUMERIC(20, 2),                     -- 退保金
    b0i1203000 NUMERIC(20, 2),                     -- 赔付支出净额
    b0i1203101 NUMERIC(20, 2),                     -- 赔付支出
    b0i1203203 NUMERIC(20, 2),                     -- 减：摊回赔付支出
    b0i1204000 NUMERIC(20, 2),                     -- 提取保险责任准备金净额
    b0i1204101 NUMERIC(20, 2),                     -- 提取保险责任准备金
    b0i1204203 NUMERIC(20, 2),                     -- 减：摊回保险责任准备金
    b0i1205000 NUMERIC(20, 2),                     -- 保单红利支出
    b0i1206000 NUMERIC(20, 2),                     -- 分保费用
    b001207000 NUMERIC(20, 2),                     -- 税金及附加
    b0f1208000 NUMERIC(20, 2),                     -- 业务及管理费
    b0i1208103 NUMERIC(20, 2),                     -- 减：摊回分保费用
    b0i1214000 NUMERIC(20, 2),                     -- 保险业务手续费及佣金支出
    b001209000 NUMERIC(20, 2),                     -- 销售费用
    b001210000 NUMERIC(20, 2),                     -- 管理费用
    b001216000 NUMERIC(20, 2),                     -- 研发费用
    b001211000 NUMERIC(20, 2),                     -- 财务费用
    b001211101 NUMERIC(20, 2),                     -- 其中：利息费用(财务费用)
    b001211203 NUMERIC(20, 2),                     -- 其中：利息收入(财务费用)
    b0f1213000 NUMERIC(20, 2),                     -- 其他业务成本
    
    -- 其他损益
    b001305000 NUMERIC(20, 2),                     -- 其他收益
    b001302000 NUMERIC(20, 2),                     -- 投资收益
    b001302101 NUMERIC(20, 2),                     -- 其中：对联营企业和合营企业的投资收益
    b001302201 NUMERIC(20, 2),                     -- 其中：以摊余成本计量的金融资产终止确认收益
    b001303000 NUMERIC(20, 2),                     -- 汇兑收益
    b001306000 NUMERIC(20, 2),                     -- 净敞口套期收益
    b001301000 NUMERIC(20, 2),                     -- 公允价值变动收益
    b001212000 NUMERIC(20, 2),                     -- 资产减值损失
    b001307000 NUMERIC(20, 2),                     -- 信用减值损失
    b001308000 NUMERIC(20, 2),                     -- 资产处置收益
    b001304000 NUMERIC(20, 2),                     -- 其他业务利润
    
    -- 利润
    b001300000 NUMERIC(20, 2),                     -- 营业利润
    b001400000 NUMERIC(20, 2),                     -- 加：营业外收入
    b001400101 NUMERIC(20, 2),                     -- 其中：非流动资产处置利得
    b001500000 NUMERIC(20, 2),                     -- 减：营业外支出
    b001500101 NUMERIC(20, 2),                     -- 其中：非流动资产处置净损益
    b001500201 NUMERIC(20, 2),                     -- 其中：非流动资产处置损失
    b001000000 NUMERIC(20, 2),                     -- 利润总额
    b002100000 NUMERIC(20, 2),                     -- 减：所得税费用
    b002200000 NUMERIC(20, 2),                     -- 未确认的投资损失
    b002300000 NUMERIC(20, 2),                     -- 影响净利润的其他项目
    
    -- 净利润
    b002000000 NUMERIC(20, 2),                     -- 净利润
    b002000401 NUMERIC(20, 2),                     -- 持续经营净利润
    b002000501 NUMERIC(20, 2),                     -- 终止经营净利润
    b002000101 NUMERIC(20, 2),                     -- 归属于母公司所有者的净利润
    b002000301 NUMERIC(20, 2),                     -- 归属于母公司其他权益工具持有者的净利润
    b002000201 NUMERIC(20, 2),                     -- 少数股东损益
    
    -- 每股收益
    b003000000 NUMERIC(10, 4),                     -- 基本每股收益
    b004000000 NUMERIC(10, 4),                     -- 稀释每股收益
    
    -- 综合收益
    b005000000 NUMERIC(20, 2),                     -- 其他综合收益(损失)
    b005000101 NUMERIC(20, 2),                     -- 归属母公司所有者的其他综合收益的税后净额
    b005000102 NUMERIC(20, 2),                     -- 归属于少数股东的其他综合收益的税后净额
    b006000000 NUMERIC(20, 2),                     -- 综合收益总额
    b006000101 NUMERIC(20, 2),                     -- 归属于母公司所有者的综合收益
    b006000103 NUMERIC(20, 2),                     -- 归属于母公司其他权益工具持有者的综合收益总额
    b006000102 NUMERIC(20, 2),                     -- 归属少数股东的综合收益
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (stkcd, accper, typrep)
);

-- 创建索引
CREATE INDEX idx_a_share_income_statement_stkcd ON a_share_income_statement(stkcd);
CREATE INDEX idx_a_share_income_statement_accper ON a_share_income_statement(accper);
CREATE INDEX idx_a_share_income_statement_short_name ON a_share_income_statement(short_name);

-- 表和字段注释
COMMENT ON TABLE a_share_income_statement IS 'A股上市公司利润表（沪深北交易所）';

-- 主键和基本字段
COMMENT ON COLUMN a_share_income_statement.stkcd IS '证券代码 - 以沪、深、北证券交易所公布的证券代码为准';
COMMENT ON COLUMN a_share_income_statement.accper IS '统计截止日期 - YYYY-MM-DD格式';
COMMENT ON COLUMN a_share_income_statement.typrep IS '报表类型 - A=合并报表，B=母公司报表';
COMMENT ON COLUMN a_share_income_statement.short_name IS '证券简称 - 以沪、深、北证券交易所公布的证券简称为准';
COMMENT ON COLUMN a_share_income_statement.if_correct IS '是否发生差错更正 - 0=否，1=是';
COMMENT ON COLUMN a_share_income_statement.declare_date IS '差错更正披露日期 - 多个日期用逗号分隔';

-- 营业收入
COMMENT ON COLUMN a_share_income_statement.b001100000 IS '营业总收入 - 企业经营过程中所有收入之和';
COMMENT ON COLUMN a_share_income_statement.b001101000 IS '营业收入 - 企业经营过程中确认的营业收入';
COMMENT ON COLUMN a_share_income_statement.bbd1102000 IS '利息净收入 - 企业所确认的利息收入与利息支出之差额';
COMMENT ON COLUMN a_share_income_statement.bbd1102101 IS '利息收入 - 企业（金融）确认的利息收入';
COMMENT ON COLUMN a_share_income_statement.bbd1102203 IS '利息支出 - 企业（金融）发生的利息支出';
COMMENT ON COLUMN a_share_income_statement.b0i1103000 IS '已赚保费 - 保险业务收入减去分出保费及提取未到期责任准备金后的余额';
COMMENT ON COLUMN a_share_income_statement.b0i1103101 IS '保险业务收入 - 从事保险业务确认的原保费收入和分保费收入';
COMMENT ON COLUMN a_share_income_statement.b0i1103111 IS '其中：分保费收入 - 从事再保险业务确认的收入';
COMMENT ON COLUMN a_share_income_statement.b0i1103203 IS '减：分出保费 - 从事再保险业务分出的保费';
COMMENT ON COLUMN a_share_income_statement.b0i1103303 IS '减：提取未到期责任准备金 - 企业（保险）提取的非寿险原保险合同未到期责任准备金';
COMMENT ON COLUMN a_share_income_statement.b0d1104000 IS '手续费及佣金净收入 - 企业确认的手续费及佣金收入与支出之差额';
COMMENT ON COLUMN a_share_income_statement.b0d1104101 IS '其中：代理买卖证券业务净收入 - 证券公司代理买卖证券业务收支差额';
COMMENT ON COLUMN a_share_income_statement.b0d1104201 IS '其中:证券承销业务净收入 - 证券公司证券承销业务收支差额';
COMMENT ON COLUMN a_share_income_statement.b0d1104301 IS '其中：受托客户资产管理业务净收入 - 证券公司受托客户资产管理业务收支差额';
COMMENT ON COLUMN a_share_income_statement.b0d1104401 IS '手续费及佣金收入 - 企业（金融）确认的手续费及佣金收入';
COMMENT ON COLUMN a_share_income_statement.b0d1104501 IS '手续费及佣金支出 - 企业（金融）发生的与经营活动相关的各项手续费、佣金支出';
COMMENT ON COLUMN a_share_income_statement.b0f1105000 IS '其他业务收入 - 企业经营的其他业务所确认的收入';

-- 营业成本
COMMENT ON COLUMN a_share_income_statement.b001200000 IS '营业总成本 - 企业经营过程中所有成本之和';
COMMENT ON COLUMN a_share_income_statement.b001201000 IS '营业成本 - 企业确认的营业成本';
COMMENT ON COLUMN a_share_income_statement.b0i1202000 IS '退保金 - 企业（保险）寿险原保险合同提前解除时退还投保人的保单现金价值';
COMMENT ON COLUMN a_share_income_statement.b0i1203000 IS '赔付支出净额 - 赔付支出减去摊回赔付支出后的余额';
COMMENT ON COLUMN a_share_income_statement.b0i1203101 IS '赔付支出 - 企业（保险）支付的原保险合同赔付款项和再保险合同赔付款项';
COMMENT ON COLUMN a_share_income_statement.b0i1203203 IS '减：摊回赔付支出 - 企业（再保险分出人）向再保险接受人摊回的赔付成本';
COMMENT ON COLUMN a_share_income_statement.b0i1204000 IS '提取保险责任准备金净额 - 提取保险责任准备金减去摊回保险责任准备金后的余额';
COMMENT ON COLUMN a_share_income_statement.b0i1204101 IS '提取保险责任准备金 - 企业提取的保险责任准备金';
COMMENT ON COLUMN a_share_income_statement.b0i1204203 IS '减：摊回保险责任准备金 - 企业（再保险分出人）应向再保险接受人摊回的保险责任准备金';
COMMENT ON COLUMN a_share_income_statement.b0i1205000 IS '保单红利支出 - 企业（保险）按原保险合同约定支付给投保人的红利';
COMMENT ON COLUMN a_share_income_statement.b0i1206000 IS '分保费用 - 企业（再保险接受人）向再保险分出人支付的分保费用';
COMMENT ON COLUMN a_share_income_statement.b001207000 IS '税金及附加 - 企业经营活动发生的营业税、消费税、城市维护建设税等相关税费';
COMMENT ON COLUMN a_share_income_statement.b0f1208000 IS '业务及管理费 - 企业（金融）在业务经营和管理过程中所发生的各项费用';
COMMENT ON COLUMN a_share_income_statement.b0i1208103 IS '减：摊回分保费用 - 企业从事再保险分出业务向再保险接受人摊回的分保费用';
COMMENT ON COLUMN a_share_income_statement.b0i1214000 IS '保险业务手续费及佣金支出 - 企业从事保险业务产生的手续费及佣金支出';
COMMENT ON COLUMN a_share_income_statement.b001209000 IS '销售费用 - 公司商品销售过程中发生的费用';
COMMENT ON COLUMN a_share_income_statement.b001210000 IS '管理费用 - 企业为组织和管理企业生产经营所发生的管理费用';
COMMENT ON COLUMN a_share_income_statement.b001216000 IS '研发费用 - 研究开发成本支出（2018年起）';
COMMENT ON COLUMN a_share_income_statement.b001211000 IS '财务费用 - 公司为筹集生产经营所需资金等而发生的费用';
COMMENT ON COLUMN a_share_income_statement.b001211101 IS '其中：利息费用(财务费用) - 企业在生产经营中进行债权性融资支付的资金占用费用（2018年起）';
COMMENT ON COLUMN a_share_income_statement.b001211203 IS '其中：利息收入(财务费用) - 企业将资金提供给他人使用取得的收入（2018年起）';
COMMENT ON COLUMN a_share_income_statement.b0f1213000 IS '其他业务成本 - 企业经营的其他业务所发生的成本';

-- 其他损益
COMMENT ON COLUMN a_share_income_statement.b001305000 IS '其他收益 - 与企业日常活动相关但不宜确认收入或冲减成本费用的政府补助（2017年起）';
COMMENT ON COLUMN a_share_income_statement.b001302000 IS '投资收益 - 公司以各种方式对外投资所取得的收益';
COMMENT ON COLUMN a_share_income_statement.b001302101 IS '其中：对联营企业和合营企业的投资收益 - 本期公司对联营企业和合营企业的投资收益';
COMMENT ON COLUMN a_share_income_statement.b001302201 IS '其中：以摊余成本计量的金融资产终止确认收益 - 因转让等情形终止确认金融资产产生的利得或损失（2019年起）';
COMMENT ON COLUMN a_share_income_statement.b001303000 IS '汇兑收益 - 企业（金融）发生的外币交易因汇率变动而产生的汇兑收益';
COMMENT ON COLUMN a_share_income_statement.b001306000 IS '净敞口套期收益 - 净敞口套期下被套期项目或现金流量套期储备转入当期损益的金额（2019年起）';
COMMENT ON COLUMN a_share_income_statement.b001301000 IS '公允价值变动收益 - 交易性金融资产、交易性金融负债等公允价值变动形成的利得或损失';
COMMENT ON COLUMN a_share_income_statement.b001212000 IS '资产减值损失 - 企业计提各项资产减值准备所形成的损失';
COMMENT ON COLUMN a_share_income_statement.b001307000 IS '信用减值损失 - 企业因应收款项无法收回而遭受的损失（2019年起）';
COMMENT ON COLUMN a_share_income_statement.b001308000 IS '资产处置收益 - 处置非流动资产产生的利得或损失（2017年起）';
COMMENT ON COLUMN a_share_income_statement.b001304000 IS '其他业务利润 - 除主营业务以外其他业务收入扣除成本、费用、税金后的利润（2007年前）';

-- 利润
COMMENT ON COLUMN a_share_income_statement.b001300000 IS '营业利润 - 与经营业务有关的利润';
COMMENT ON COLUMN a_share_income_statement.b001400000 IS '加：营业外收入 - 企业发生的各项营业外收入';
COMMENT ON COLUMN a_share_income_statement.b001400101 IS '其中：非流动资产处置利得 - 包括固定资产处置利得和无形资产出售利得（2015年起）';
COMMENT ON COLUMN a_share_income_statement.b001500000 IS '减：营业外支出 - 企业发生的各项营业外支出';
COMMENT ON COLUMN a_share_income_statement.b001500101 IS '其中：非流动资产处置净损益 - 年度内处置非流动资产产生的净损益合计';
COMMENT ON COLUMN a_share_income_statement.b001500201 IS '其中：非流动资产处置损失 - 包括固定资产处置损失和无形资产出售损失（2015年起）';
COMMENT ON COLUMN a_share_income_statement.b001000000 IS '利润总额 - 公司实现的利润总额';
COMMENT ON COLUMN a_share_income_statement.b002100000 IS '减：所得税费用 - 企业确认的应从当期利润总额中扣除的所得税费用';
COMMENT ON COLUMN a_share_income_statement.b002200000 IS '未确认的投资损失 - 按权益法核算长期投资，被投资企业负所有者权益之份额（2007年前）';
COMMENT ON COLUMN a_share_income_statement.b002300000 IS '影响净利润的其他项目 - 影响净利润的其他项目';

-- 净利润
COMMENT ON COLUMN a_share_income_statement.b002000000 IS '净利润 - 公司实现的净利润';
COMMENT ON COLUMN a_share_income_statement.b002000401 IS '持续经营净利润 - 持续经营业务产生的净利润';
COMMENT ON COLUMN a_share_income_statement.b002000501 IS '终止经营净利润 - 终止经营业务产生的净利润';
COMMENT ON COLUMN a_share_income_statement.b002000101 IS '归属于母公司所有者的净利润 - 合并报表净利润中归属于母公司所有者的净利润';
COMMENT ON COLUMN a_share_income_statement.b002000301 IS '归属于母公司其他权益工具持有者的净利润 - 归属于母公司的子公司发行优先股等权益工具产生的净利润（2018年起）';
COMMENT ON COLUMN a_share_income_statement.b002000201 IS '少数股东损益 - 子公司年度损益中按少数股东股权比例计算的应属少数股东享有的利润或分担的亏损';

-- 每股收益
COMMENT ON COLUMN a_share_income_statement.b003000000 IS '基本每股收益 - 归属于普通股股东的当期净利润除以发行在外普通股的加权平均数';
COMMENT ON COLUMN a_share_income_statement.b004000000 IS '稀释每股收益 - 考虑稀释性潜在普通股影响后的每股收益';

-- 综合收益
COMMENT ON COLUMN a_share_income_statement.b005000000 IS '其他综合收益(损失) - 根据企业会计准则规定未在损益中确认的各项利得和损失扣除所得税后的净额';
COMMENT ON COLUMN a_share_income_statement.b005000101 IS '归属母公司所有者的其他综合收益的税后净额 - 归属母公司部分的其他综合收益';
COMMENT ON COLUMN a_share_income_statement.b005000102 IS '归属于少数股东的其他综合收益的税后净额 - 归属少数股东部分的其他综合收益';
COMMENT ON COLUMN a_share_income_statement.b006000000 IS '综合收益总额 - 除所有者出资额和代收款项以外的各种收入';
COMMENT ON COLUMN a_share_income_statement.b006000101 IS '归属于母公司所有者的综合收益 - 综合收益中归属于母公司所有者享有的部分';
COMMENT ON COLUMN a_share_income_statement.b006000103 IS '归属于母公司其他权益工具持有者的综合收益总额 - 综合收益中归属于母公司其他权益工具持有者的部分';
COMMENT ON COLUMN a_share_income_statement.b006000102 IS '归属少数股东的综合收益 - 少数股东按照权益比例在综合损益中所占用的利润分配';

-- 审计字段
COMMENT ON COLUMN a_share_income_statement.created_at IS '记录创建时间';
COMMENT ON COLUMN a_share_income_statement.updated_at IS '记录更新时间';

-- =====================================================
-- 3. A股现金流量表 (A-Share Cash Flow Statement)
-- =====================================================

CREATE TABLE IF NOT EXISTS a_share_cashflow_statement (
    -- 主键字段
    stkcd VARCHAR(10) NOT NULL,                    -- 证券代码
    accper DATE NOT NULL,                          -- 统计截止日期
    typrep CHAR(1) NOT NULL,                       -- 报表类型：A=合并报表，B=母公司报表
    
    -- 基本信息
    short_name VARCHAR(100),                       -- 证券简称
    if_correct SMALLINT DEFAULT 0,                 -- 是否发生差错更正：0=否，1=是
    declare_date VARCHAR(200),                     -- 差错更正披露日期
    
    -- 经营活动现金流量
    c001001000 NUMERIC(20, 2),                     -- 销售商品、提供劳务收到的现金
    c0b1002000 NUMERIC(20, 2),                     -- 客户存款和同业存放款项净增加额
    c0f1023000 NUMERIC(20, 2),                     -- 存放央行和同业款项净减少额
    c0b1003000 NUMERIC(20, 2),                     -- 向中央银行借款净增加额
    c0b1004000 NUMERIC(20, 2),                     -- 向其他金融机构拆入资金净增加额
    c0i1005000 NUMERIC(20, 2),                     -- 收到原保险合同保费取得的现金
    c0i1006000 NUMERIC(20, 2),                     -- 收到再保险业务现金净额
    c0i1007000 NUMERIC(20, 2),                     -- 保户储金及投资款净增加额
    c0d1008000 NUMERIC(20, 2),                     -- 处置交易性金融资产净增加额
    c0f1009000 NUMERIC(20, 2),                     -- 收取利息、手续费及佣金的现金
    c0d1010000 NUMERIC(20, 2),                     -- 拆入资金净增加额
    c0d1011000 NUMERIC(20, 2),                     -- 回购业务资金净增加额
    c0f1024000 NUMERIC(20, 2),                     -- 拆出资金净减少额
    c0f1025000 NUMERIC(20, 2),                     -- 买入返售款项净减少额
    c001012000 NUMERIC(20, 2),                     -- 收到的税费返还
    c001013000 NUMERIC(20, 2),                     -- 收到的其他与经营活动有关的现金
    c001100000 NUMERIC(20, 2),                     -- 经营活动现金流入小计
    
    c001014000 NUMERIC(20, 2),                     -- 购买商品、接受劳务支付的现金
    c0b1015000 NUMERIC(20, 2),                     -- 客户贷款及垫款净增加额
    c0f1026000 NUMERIC(20, 2),                     -- 向中央银行借款净减少额
    c0b1016000 NUMERIC(20, 2),                     -- 存放中央银行和同业款项净增加额
    c0i1017000 NUMERIC(20, 2),                     -- 支付原保险合同赔付款项的现金
    c0f1018000 NUMERIC(20, 2),                     -- 支付利息、手续费及佣金的现金
    c0f1027000 NUMERIC(20, 2),                     -- 支付再保业务现金净额
    c0f1028000 NUMERIC(20, 2),                     -- 保户储金及投资款净减少额
    c0f1029000 NUMERIC(20, 2),                     -- 拆出资金净增加额
    c0f1030000 NUMERIC(20, 2),                     -- 买入返售款项净增加额
    c0f1031000 NUMERIC(20, 2),                     -- 拆入资金净减少额
    c0f1032000 NUMERIC(20, 2),                     -- 卖出回购款项净减少额
    c0i1019000 NUMERIC(20, 2),                     -- 支付保单红利的现金
    c001020000 NUMERIC(20, 2),                     -- 支付给职工以及为职工支付的现金
    c001021000 NUMERIC(20, 2),                     -- 支付的各项税费
    c001022000 NUMERIC(20, 2),                     -- 支付其他与经营活动有关的现金
    c001200000 NUMERIC(20, 2),                     -- 经营活动现金流出小计
    c001000000 NUMERIC(20, 2),                     -- 经营活动产生的现金流量净额
    
    -- 投资活动现金流量
    c002001000 NUMERIC(20, 2),                     -- 收回投资收到的现金
    c002002000 NUMERIC(20, 2),                     -- 取得投资收益收到的现金
    c002003000 NUMERIC(20, 2),                     -- 处置固定资产、无形资产和其他长期资产收回的现金净额
    c002004000 NUMERIC(20, 2),                     -- 处置子公司及其他营业单位收到的现金净额
    c002005000 NUMERIC(20, 2),                     -- 收到的其他与投资活动有关的现金
    c002100000 NUMERIC(20, 2),                     -- 投资活动产生的现金流入小计
    
    c002006000 NUMERIC(20, 2),                     -- 购建固定资产、无形资产和其他长期资产支付的现金
    c002007000 NUMERIC(20, 2),                     -- 投资支付的现金
    c0i2008000 NUMERIC(20, 2),                     -- 质押贷款净增加额
    c002009000 NUMERIC(20, 2),                     -- 取得子公司及其他营业单位支付的现金净额
    c002010000 NUMERIC(20, 2),                     -- 支付其他与投资活动有关的现金
    c002200000 NUMERIC(20, 2),                     -- 投资活动产生的现金流出小计
    c002000000 NUMERIC(20, 2),                     -- 投资活动产生的现金流量净额
    
    -- 筹资活动现金流量
    c003008000 NUMERIC(20, 2),                     -- 吸收投资收到的现金
    c003001000 NUMERIC(20, 2),                     -- 吸收权益性投资收到的现金
    c003001101 NUMERIC(20, 2),                     -- 其中：子公司吸收少数股东投资收到的现金
    c003003000 NUMERIC(20, 2),                     -- 发行债券收到的现金
    c003002000 NUMERIC(20, 2),                     -- 取得借款收到的现金
    c003004000 NUMERIC(20, 2),                     -- 收到其他与筹资活动有关的现金
    c003100000 NUMERIC(20, 2),                     -- 筹资活动现金流入小计
    
    c003005000 NUMERIC(20, 2),                     -- 偿还债务支付的现金
    c003006000 NUMERIC(20, 2),                     -- 分配股利、利润或偿付利息支付的现金
    c003006101 NUMERIC(20, 2),                     -- 其中：子公司支付给少数股东的股利、利润
    c003007000 NUMERIC(20, 2),                     -- 支付其他与筹资活动有关的现金
    c003200000 NUMERIC(20, 2),                     -- 筹资活动现金流出小计
    c003000000 NUMERIC(20, 2),                     -- 筹资活动产生的现金流量净额
    
    -- 其他
    c004000000 NUMERIC(20, 2),                     -- 汇率变动对现金及现金等价物的影响
    c007000000 NUMERIC(20, 2),                     -- 其他对现金的影响
    c005000000 NUMERIC(20, 2),                     -- 现金及现金等价物净增加额
    c005001000 NUMERIC(20, 2),                     -- 期初现金及现金等价物余额
    c006000000 NUMERIC(20, 2),                     -- 期末现金及现金等价物余额
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (stkcd, accper, typrep)
);

-- 创建索引
CREATE INDEX idx_a_share_cashflow_statement_stkcd ON a_share_cashflow_statement(stkcd);
CREATE INDEX idx_a_share_cashflow_statement_accper ON a_share_cashflow_statement(accper);
CREATE INDEX idx_a_share_cashflow_statement_short_name ON a_share_cashflow_statement(short_name);

-- 表和字段注释
COMMENT ON TABLE a_share_cashflow_statement IS 'A股上市公司现金流量表（沪深北交易所）';

-- 主键和基本字段
COMMENT ON COLUMN a_share_cashflow_statement.stkcd IS '证券代码 - 以沪、深、北证券交易所公布的证券代码为准';
COMMENT ON COLUMN a_share_cashflow_statement.accper IS '统计截止日期 - YYYY-MM-DD格式';
COMMENT ON COLUMN a_share_cashflow_statement.typrep IS '报表类型 - A=合并报表，B=母公司报表';
COMMENT ON COLUMN a_share_cashflow_statement.short_name IS '证券简称 - 以沪、深、北证券交易所公布的证券简称为准';
COMMENT ON COLUMN a_share_cashflow_statement.if_correct IS '是否发生差错更正 - 0=否，1=是';
COMMENT ON COLUMN a_share_cashflow_statement.declare_date IS '差错更正披露日期 - 多个日期用逗号分隔';

-- 经营活动现金流入
COMMENT ON COLUMN a_share_cashflow_statement.c001001000 IS '销售商品、提供劳务收到的现金 - 销售商品、提供劳务实际收到的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c0b1002000 IS '客户存款和同业存放款项净增加额 - 本期吸收的各种存款的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1023000 IS '存放央行和同业款项净减少额 - 本期存放于中央银行及金融机构款项的净减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0b1003000 IS '向中央银行借款净增加额 - 本期向中央银行借入款项的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0b1004000 IS '向其他金融机构拆入资金净增加额 - 从境内外金融机构拆入款项的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0i1005000 IS '收到原保险合同保费取得的现金 - 保险公司收到的原保险合同保费（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0i1006000 IS '收到再保险业务现金净额 - 从事再保险业务实际收到的款项（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0i1007000 IS '保户储金及投资款净增加额 - 实际向投保人收取的储金及投资本金（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0d1008000 IS '处置交易性金融资产净增加额 - 证券公司自行买卖交易性金融资产所取得的现金净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1009000 IS '收取利息、手续费及佣金的现金 - 本期收到的利息、手续费和佣金（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0d1010000 IS '拆入资金净增加额 - 从境内外金融机构拆入款项所取得的现金的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0d1011000 IS '回购业务资金净增加额 - 按回购协议融入资金减去返售金融资产融出资金后的净额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1024000 IS '拆出资金净减少额 - 拆借给其他金融机构的款项的净减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1025000 IS '买入返售款项净减少额 - 按返售协议约定先买入再按固定价格返售的款项的净减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c001012000 IS '收到的税费返还 - 收到返还的各种税费';
COMMENT ON COLUMN a_share_cashflow_statement.c001013000 IS '收到的其他与经营活动有关的现金 - 除上述各项目外，收到的其他与经营活动有关的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c001100000 IS '经营活动现金流入小计 - 经营活动现金流入各项目合计';

-- 经营活动现金流出
COMMENT ON COLUMN a_share_cashflow_statement.c001014000 IS '购买商品、接受劳务支付的现金 - 购买商品、接受劳务实际支付的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c0b1015000 IS '客户贷款及垫款净增加额 - 发放的各种客户贷款、商业票据贴现等业务的款项净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1026000 IS '向中央银行借款净减少额 - 向中央银行借入款项的净减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0b1016000 IS '存放中央银行和同业款项净增加额 - 存放于中央银行及金融机构的款项的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0i1017000 IS '支付原保险合同赔付款项的现金 - 保险公司实际支付原保险合同赔付的现金（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1018000 IS '支付利息、手续费及佣金的现金 - 实际支付的利息、手续费和佣金流出（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1027000 IS '支付再保业务现金净额 - 从事再保险业务实际支付的款项（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1028000 IS '保户储金及投资款净减少额 - 实际向投保人支付的储金及投资本金的减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1029000 IS '拆出资金净增加额 - 拆借给其他金融机构的款项的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1030000 IS '买入返售款项净增加额 - 按返售协议约定先买入再按固定价格返售的款项的净增加额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1031000 IS '拆入资金净减少额 - 从金融机构拆入款项的净减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0f1032000 IS '卖出回购款项净减少额 - 按回购协议卖出金融资产所融入的资金的净减少额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c0i1019000 IS '支付保单红利的现金 - 企业（保险）按原保险合同约定实际支付给投保人的红利（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c001020000 IS '支付给职工以及为职工支付的现金 - 实际支付给职工的工资、奖金、各种津贴和补贴等';
COMMENT ON COLUMN a_share_cashflow_statement.c001021000 IS '支付的各项税费 - 本期发生并支付的、本期支付以前各期发生的以及预交的各项税费';
COMMENT ON COLUMN a_share_cashflow_statement.c001022000 IS '支付其他与经营活动有关的现金 - 除上述各项目外，支付的其他与经营活动有关的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c001200000 IS '经营活动现金流出小计 - 经营活动现金流出各项目合计';
COMMENT ON COLUMN a_share_cashflow_statement.c001000000 IS '经营活动产生的现金流量净额 - 经营活动现金流入减去经营活动现金流出的差额';

-- 投资活动现金流量
COMMENT ON COLUMN a_share_cashflow_statement.c002001000 IS '收回投资收到的现金 - 出售、转让或到期收回非现金等价物的投资而收到的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c002002000 IS '取得投资收益收到的现金 - 因股权性投资和债权性投资而取得的现金股利、利息';
COMMENT ON COLUMN a_share_cashflow_statement.c002003000 IS '处置固定资产、无形资产和其他长期资产收回的现金净额 - 出售固定资产、无形资产和其他长期资产收回的现金净额';
COMMENT ON COLUMN a_share_cashflow_statement.c002004000 IS '处置子公司及其他营业单位收到的现金净额 - 本期购买和处置子公司及其他营业单位所收到的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c002005000 IS '收到的其他与投资活动有关的现金 - 除上述各项以外，收到的其他与投资活动有关的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c002100000 IS '投资活动产生的现金流入小计 - 投资活动现金流入各项目合计';
COMMENT ON COLUMN a_share_cashflow_statement.c002006000 IS '购建固定资产、无形资产和其他长期资产支付的现金 - 购买、建造固定资产，取得无形资产和其他长期资产支付的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c002007000 IS '投资支付的现金 - 进行权益性投资和债权性投资支付的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c0i2008000 IS '质押贷款净增加额 - 本期发放保户质押贷款的净额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c002009000 IS '取得子公司及其他营业单位支付的现金净额 - 本期购买和处置子公司及其他营业单位所支付的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c002010000 IS '支付其他与投资活动有关的现金 - 除上述各项以外，支付的其他与投资活动有关的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c002200000 IS '投资活动产生的现金流出小计 - 投资活动现金流出各项目合计';
COMMENT ON COLUMN a_share_cashflow_statement.c002000000 IS '投资活动产生的现金流量净额 - 投资活动现金流入减去投资活动现金流出的差额';

-- 筹资活动现金流量
COMMENT ON COLUMN a_share_cashflow_statement.c003008000 IS '吸收投资收到的现金 - 以发行股票、债券等方式筹集的资金实际收到的款项净额';
COMMENT ON COLUMN a_share_cashflow_statement.c003001000 IS '吸收权益性投资收到的现金 - 以发行股票方式筹集资金实际收到的股款净额';
COMMENT ON COLUMN a_share_cashflow_statement.c003001101 IS '其中：子公司吸收少数股东投资收到的现金 - 合并报表中子公司吸收少数股东投资收到的现金净额';
COMMENT ON COLUMN a_share_cashflow_statement.c003003000 IS '发行债券收到的现金 - 通过发行债券筹集资金所收到的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c003002000 IS '取得借款收到的现金 - 向银行或其他金融机构等借入的资金';
COMMENT ON COLUMN a_share_cashflow_statement.c003004000 IS '收到其他与筹资活动有关的现金 - 除上述各项目外，收到的其他与筹资活动有关的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c003100000 IS '筹资活动现金流入小计 - 筹资活动现金流入各项目合计';
COMMENT ON COLUMN a_share_cashflow_statement.c003005000 IS '偿还债务支付的现金 - 以现金偿还债务的本金';
COMMENT ON COLUMN a_share_cashflow_statement.c003006000 IS '分配股利、利润或偿付利息支付的现金 - 实际支付的现金股利、利润或借款利息、债券利息';
COMMENT ON COLUMN a_share_cashflow_statement.c003006101 IS '其中：子公司支付给少数股东的股利、利润 - 合并报表中子公司支付给其少数股东的股利、利润';
COMMENT ON COLUMN a_share_cashflow_statement.c003007000 IS '支付其他与筹资活动有关的现金 - 除上述各项外，支付的其他与筹资活动有关的现金';
COMMENT ON COLUMN a_share_cashflow_statement.c003200000 IS '筹资活动现金流出小计 - 筹资活动现金流出各项目合计';
COMMENT ON COLUMN a_share_cashflow_statement.c003000000 IS '筹资活动产生的现金流量净额 - 筹资活动现金流入减去筹资活动现金流出的差额';

-- 其他项目
COMMENT ON COLUMN a_share_cashflow_statement.c004000000 IS '汇率变动对现金及现金等价物的影响 - 外币现金流量按折算汇率折算的人民币金额与外币现金净额按期末汇率折算的人民币金额之间的差额';
COMMENT ON COLUMN a_share_cashflow_statement.c007000000 IS '其他对现金的影响 - 其他影响现金的科目';
COMMENT ON COLUMN a_share_cashflow_statement.c005000000 IS '现金及现金等价物净增加额 - 会计期间内现金及现金等价物净增加额';
COMMENT ON COLUMN a_share_cashflow_statement.c005001000 IS '期初现金及现金等价物余额 - 期初现金及现金等价物的余额（2007年起）';
COMMENT ON COLUMN a_share_cashflow_statement.c006000000 IS '期末现金及现金等价物余额 - 期末现金及现金等价物的余额（2007年起）';

-- 审计字段
COMMENT ON COLUMN a_share_cashflow_statement.created_at IS '记录创建时间';
COMMENT ON COLUMN a_share_cashflow_statement.updated_at IS '记录更新时间';

-- =====================================================
-- 4. 辅助视图：联合查询所有报表
-- =====================================================

CREATE OR REPLACE VIEW v_a_share_financial_reports AS
SELECT 
    b.stkcd,
    b.short_name,
    b.accper,
    b.typrep,
    b.a001000000 AS total_assets,                  -- 资产总计
    b.a002000000 AS total_liabilities,             -- 负债合计
    b.a003000000 AS total_equity,                  -- 所有者权益合计
    i.b001101000 AS operating_revenue,             -- 营业收入
    i.b001300000 AS operating_profit,              -- 营业利润
    i.b002000000 AS net_profit,                    -- 净利润
    i.b002000101 AS net_profit_parent,             -- 归属母公司净利润
    c.c001000000 AS operating_cash_flow,           -- 经营活动现金流量净额
    c.c002000000 AS investing_cash_flow,           -- 投资活动现金流量净额
    c.c003000000 AS financing_cash_flow            -- 筹资活动现金流量净额
FROM a_share_balance_sheet b
LEFT JOIN a_share_income_statement i ON b.stkcd = i.stkcd AND b.accper = i.accper AND b.typrep = i.typrep
LEFT JOIN a_share_cashflow_statement c ON b.stkcd = c.stkcd AND b.accper = c.accper AND b.typrep = c.typrep;

COMMENT ON VIEW v_a_share_financial_reports IS 'A股上市公司财务报表汇总视图（沪深北交易所）';

-- =====================================================
-- 5. 更新时间触发器
-- =====================================================

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为三张表添加触发器
CREATE TRIGGER update_a_share_balance_sheet_updated_at
    BEFORE UPDATE ON a_share_balance_sheet
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_a_share_income_statement_updated_at
    BEFORE UPDATE ON a_share_income_statement
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_a_share_cashflow_statement_updated_at
    BEFORE UPDATE ON a_share_cashflow_statement
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 6. 示例查询
-- =====================================================

-- 查询某公司最近一期财报（示例：浦发银行 600000）
-- SELECT * FROM v_a_share_financial_reports 
-- WHERE stkcd = '600000' 
-- AND typrep = 'A'
-- ORDER BY accper DESC 
-- LIMIT 1;

-- 查询某公司历史趋势
-- SELECT 
--     accper,
--     operating_revenue,
--     net_profit,
--     operating_cash_flow
-- FROM v_a_share_financial_reports
-- WHERE stkcd = '600000'
-- AND typrep = 'A'
-- ORDER BY accper DESC;

-- =====================================================
-- 完成
-- =====================================================

