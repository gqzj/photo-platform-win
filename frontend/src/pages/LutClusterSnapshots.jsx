import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Tag,
  Typography,
  Row,
  Col,
  Image,
  Pagination,
  Empty,
  Spin,
  Popconfirm,
  Tree,
  Modal
} from 'antd'
import { EyeOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

const LutClusterSnapshots = () => {
  const [loading, setLoading] = useState(false)
  const [snapshots, setSnapshots] = useState([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewSnapshot, setPreviewSnapshot] = useState(null)
  const [selectedClusterId, setSelectedClusterId] = useState(null)
  const [clusterFiles, setClusterFiles] = useState([])
  const [clusterFilesLoading, setClusterFilesLoading] = useState(false)
  const [clusterFilesPagination, setClusterFilesPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [previewFile, setPreviewFile] = useState(null)
  const [previewModalFileVisible, setPreviewModalFileVisible] = useState(false)

  useEffect(() => {
    fetchSnapshots()
  }, [pagination.current])

  const fetchSnapshots = async () => {
    setLoading(true)
    try {
      const response = await api.get('/lut-files/cluster/snapshots', {
        params: {
          page: pagination.current,
          page_size: pagination.pageSize
        }
      })
      if (response.code === 200) {
        setSnapshots(response.data.list || [])
        setPagination({
          ...pagination,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取快照列表失败')
      }
    } catch (error) {
      message.error('获取快照列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async (snapshot) => {
    try {
      const response = await api.get(`/lut-files/cluster/snapshot/${snapshot.id}`)
      if (response.code === 200) {
        setPreviewSnapshot(response.data)
        setPreviewModalVisible(true)
        // 重置选择
        setSelectedClusterId(null)
        setClusterFiles([])
      } else {
        message.error(response.message || '获取快照详情失败')
      }
    } catch (error) {
      message.error('获取快照详情失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handlePageChange = (page) => {
    setPagination({ ...pagination, current: page })
  }

  const handleDelete = async (snapshot) => {
    try {
      const response = await api.delete(`/lut-files/cluster/snapshot/${snapshot.id}`)
      if (response.code === 200) {
        message.success('删除成功')
        // 刷新列表
        await fetchSnapshots()
        // 如果删除的是当前预览的快照，关闭预览
        if (previewSnapshot && previewSnapshot.id === snapshot.id) {
          setPreviewModalVisible(false)
          setPreviewSnapshot(null)
        }
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  const fetchClusterFiles = async (clusterId, page = 1) => {
    setClusterFilesLoading(true)
    try {
      // clusterId可能是字符串（如"1-4"）或数字
      const clusterIdStr = typeof clusterId === 'string' ? clusterId : clusterId.toString()
      const response = await api.get(`/lut-files/cluster/${clusterIdStr}/files`, {
        params: {
          page: page,
          page_size: clusterFilesPagination.pageSize
        }
      })

      if (response.code === 200) {
        setClusterFiles(response.data.list || [])
        setClusterFilesPagination({
          ...clusterFilesPagination,
          current: response.data.page,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取文件列表失败')
      }
    } catch (error) {
      message.error('获取文件列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setClusterFilesLoading(false)
    }
  }

  const handleClusterClick = (clusterId) => {
    setSelectedClusterId(clusterId)
    fetchClusterFiles(clusterId, 1)
  }

  const handleClusterFilesPageChange = (page) => {
    fetchClusterFiles(selectedClusterId, page)
  }

  const handlePreviewFile = (file) => {
    setPreviewFile(file)
    setPreviewModalFileVisible(true)
  }

  const getClusterColor = (clusterId) => {
    const colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'gold', 'lime', 'volcano']
    const clusterIdStr = String(clusterId)
    const clusterIdNum = clusterIdStr.includes('-') ? parseInt(clusterIdStr.split('-')[0]) : parseInt(clusterIdStr)
    return colors[clusterIdNum % colors.length]
  }

  // 构建聚类树结构（与LutClusterAnalysis.jsx一致）
  const buildClusterTree = (clusterData) => {
    if (!clusterData) return []
    
    const treeData = []
    const clusterMap = new Map()
    
    // 首先创建所有节点
    Object.entries(clusterData).forEach(([clusterId, clusterInfo]) => {
      const path = clusterInfo.path || clusterId
      const level = clusterInfo.level !== undefined ? clusterInfo.level : (path.split('-').length - 1)
      const count = clusterInfo.file_count || 0
      const clusterName = clusterInfo.cluster_name || null
      
      clusterMap.set(path, {
        clusterId: path,
        count: count,
        level: level,
        clusterName: clusterName,
        children: []
      })
    })
    
    // 构建树结构
    clusterMap.forEach((node, path) => {
      if (node.level === 0) {
        // 顶级节点
        treeData.push({
          key: path,
          clusterId: path,
          count: node.count,
          clusterName: node.clusterName,
          children: []
        })
      } else {
        // 子节点，找到父节点
        const parts = path.split('-')
        const parentPath = parts.slice(0, -1).join('-')
        const parentNode = clusterMap.get(parentPath)
        if (parentNode) {
          if (!parentNode.children) {
            parentNode.children = []
          }
          parentNode.children.push({
            key: path,
            clusterId: path,
            count: node.count,
            clusterName: node.clusterName,
            children: []
          })
        }
      }
    })
    
    // 递归添加子节点到树结构
    const addChildren = (nodes) => {
      nodes.forEach(node => {
        const clusterInfo = clusterMap.get(node.clusterId)
        if (clusterInfo && clusterInfo.children) {
          node.children = clusterInfo.children
          if (node.children.length > 0) {
            addChildren(node.children)
          }
        }
      })
    }
    
    addChildren(treeData)
    
    return treeData
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '快照名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '聚类指标',
      dataIndex: 'metric_name',
      key: 'metric_name',
      width: 150
    },
    {
      title: '聚类算法',
      dataIndex: 'algorithm_name',
      key: 'algorithm_name',
      width: 150
    },
    {
      title: '聚类数',
      dataIndex: 'n_clusters',
      key: 'n_clusters',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个快照吗？"
            description="删除后无法恢复"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>LUT聚类快照</Title>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchSnapshots}
              loading={loading}
            >
              刷新
            </Button>
          </div>

          <Table
            columns={columns}
            dataSource={snapshots}
            rowKey="id"
            loading={loading}
            pagination={false}
          />

          {pagination.total > 0 && (
            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <Pagination
                current={pagination.current}
                pageSize={pagination.pageSize}
                total={pagination.total}
                onChange={handlePageChange}
                showTotal={(total) => `共 ${total} 条`}
                showSizeChanger={false}
              />
            </div>
          )}
        </Space>
      </Card>

      {/* 快照详情模态框 - 使用与LutClusterAnalysis.jsx一致的布局 */}
      <Modal
        title={`快照详情：${previewSnapshot?.name || ''}`}
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false)
          setPreviewSnapshot(null)
          setSelectedClusterId(null)
          setClusterFiles([])
        }}
        footer={null}
        width="90%"
        style={{ top: 20 }}
      >
        {previewSnapshot && (
          <div>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                {previewSnapshot.description && (
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>快照描述：</Text>
                    <Text>{previewSnapshot.description}</Text>
                  </div>
                )}
                <div>
                  <Text strong>聚类指标：</Text>
                  <Tag color="blue">{previewSnapshot.metric_name || '未知'}</Tag>
                  <Text strong style={{ marginLeft: 16 }}>聚类算法：</Text>
                  <Tag color="green">{previewSnapshot.algorithm_name || '未知'}</Tag>
                  <Text strong style={{ marginLeft: 16 }}>聚类数：</Text>
                  <Tag>{previewSnapshot.n_clusters}</Tag>
                  <Text strong style={{ marginLeft: 16 }}>创建时间：</Text>
                  <Text>{previewSnapshot.created_at}</Text>
                </div>
              </div>

              {previewSnapshot.cluster_data && (
                <Row gutter={16} style={{ height: 'calc(100vh - 300px)' }}>
                  {/* 左侧：聚类统计树（只读） */}
                  <Col span={10} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Card 
                      title="聚类统计" 
                      size="small"
                      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                      bodyStyle={{ flex: 1, overflow: 'auto', padding: '16px' }}
                    >
                      <Space direction="vertical" size="small" style={{ width: '100%', marginBottom: 16 }}>
                        <div>
                          <Text strong>总聚类数：</Text>
                          <Text>{Object.keys(previewSnapshot.cluster_data).length}</Text>
                          <Text strong style={{ marginLeft: 16 }}>总文件数：</Text>
                          <Text>
                            {Object.values(previewSnapshot.cluster_data).reduce((sum, info) => sum + (info.file_count || 0), 0)}
                          </Text>
                        </div>
                        <div>
                          <Text strong>聚类指标：</Text>
                          <Tag color="blue">{previewSnapshot.metric_name || '未知'}</Tag>
                          <Text strong style={{ marginLeft: 16 }}>聚类算法：</Text>
                          <Tag color="green">{previewSnapshot.algorithm_name || '未知'}</Tag>
                        </div>
                      </Space>
                      <Tree
                        showLine
                        defaultExpandAll
                        treeData={buildClusterTree(previewSnapshot.cluster_data)}
                        titleRender={(nodeData) => {
                          const clusterId = nodeData.clusterId
                          const count = nodeData.count
                          const clusterName = nodeData.clusterName
                          const clusterIdStr = String(clusterId)
                          const clusterIdNum = clusterIdStr.includes('-') ? parseInt(clusterIdStr.split('-')[0]) : parseInt(clusterIdStr)
                          const isSelected = selectedClusterId === clusterId || selectedClusterId === clusterIdStr
                          
                          return (
                            <div
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '4px 8px',
                                backgroundColor: isSelected ? '#e6f7ff' : 'transparent',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                width: '100%'
                              }}
                              onClick={() => handleClusterClick(clusterId)}
                            >
                              <Space>
                                <Tag color={getClusterColor(clusterIdNum)}>
                                  {clusterName || `聚类 ${clusterIdStr}`}
                                </Tag>
                                <Text type="secondary">({count} 个文件)</Text>
                              </Space>
                            </div>
                          )
                        }}
                      />
                    </Card>
                  </Col>

                  {/* 右侧：文件列表（只读） */}
                  <Col span={14} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    {selectedClusterId !== null ? (
                      <Card 
                        title={`聚类 ${selectedClusterId} 的文件列表`}
                        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                        bodyStyle={{ flex: 1, overflow: 'auto', padding: '16px' }}
                      >
                        <Spin spinning={clusterFilesLoading}>
                          {clusterFiles.length > 0 ? (
                            <>
                              <Row gutter={[16, 16]}>
                                {clusterFiles.map((file) => (
                                  <Col xs={12} sm={8} md={6} lg={6} xl={6} key={file.id}>
                                    <Card
                                      hoverable
                                      style={{
                                        height: '100%',
                                        display: 'flex',
                                        flexDirection: 'column'
                                      }}
                                      bodyStyle={{
                                        padding: '8px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        flex: 1
                                      }}
                                      cover={
                                        file.thumbnail_path ? (
                                          <div 
                                            style={{ 
                                              width: '100%', 
                                              height: '180px', 
                                              display: 'flex', 
                                              alignItems: 'center', 
                                              justifyContent: 'center',
                                              backgroundColor: '#f5f5f5',
                                              overflow: 'hidden',
                                              cursor: 'pointer'
                                            }}
                                            onClick={() => handlePreviewFile(file)}
                                          >
                                            <Image
                                              src={`/api/lut-files/${file.id}/thumbnail`}
                                              alt={file.original_filename}
                                              style={{ 
                                                width: '100%', 
                                                height: '100%', 
                                                objectFit: 'cover' 
                                              }}
                                              preview={false}
                                            />
                                          </div>
                                        ) : (
                                          <div style={{ 
                                            width: '100%', 
                                            height: '180px', 
                                            display: 'flex', 
                                            alignItems: 'center', 
                                            justifyContent: 'center',
                                            backgroundColor: '#f5f5f5',
                                            color: '#999'
                                          }}>
                                            无缩略图
                                          </div>
                                        )
                                      }
                                    >
                                      <div style={{ flex: 1 }}>
                                        <Typography.Text
                                          strong
                                          ellipsis
                                          style={{
                                            display: 'block',
                                            marginBottom: '4px',
                                            fontSize: '12px'
                                          }}
                                          title={file.original_filename}
                                        >
                                          {file.original_filename}
                                        </Typography.Text>
                                        <div style={{ marginBottom: '4px' }}>
                                          <Text type="secondary" style={{ fontSize: '10px' }}>
                                            ID: {file.id}
                                          </Text>
                                        </div>
                                        {file.category_name && (
                                          <div style={{ marginBottom: '4px' }}>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                              {file.category_name}
                                            </Text>
                                          </div>
                                        )}
                                      </div>
                                    </Card>
                                  </Col>
                                ))}
                              </Row>
                              {clusterFilesPagination.total > clusterFilesPagination.pageSize && (
                                <div style={{ marginTop: '24px', textAlign: 'center' }}>
                                  <Pagination
                                    current={clusterFilesPagination.current}
                                    pageSize={clusterFilesPagination.pageSize}
                                    total={clusterFilesPagination.total}
                                    onChange={handleClusterFilesPageChange}
                                    showTotal={(total) => `共 ${total} 条`}
                                    showSizeChanger={false}
                                  />
                                </div>
                              )}
                            </>
                          ) : (
                            <Empty description="该聚类暂无文件" />
                          )}
                        </Spin>
                      </Card>
                    ) : (
                      <Card 
                        title="文件列表"
                        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                        bodyStyle={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                      >
                        <Empty description="请从左侧选择聚类查看文件列表" />
                      </Card>
                    )}
                  </Col>
                </Row>
              )}
            </Space>
          </div>
        )}
      </Modal>

      {/* 文件预览模态框 */}
      <Modal
        title={previewFile?.original_filename || '文件预览'}
        open={previewModalFileVisible}
        onCancel={() => {
          setPreviewModalFileVisible(false)
          setPreviewFile(null)
        }}
        footer={null}
        width={800}
      >
        {previewFile && (
          <div>
            <Image
              src={`/api/lut-files/${previewFile.id}/thumbnail`}
              alt={previewFile.original_filename}
              style={{ width: '100%' }}
            />
            <div style={{ marginTop: 16 }}>
              <Text strong>文件名：</Text>
              <Text>{previewFile.original_filename}</Text>
            </div>
            <div style={{ marginTop: 8 }}>
              <Text strong>文件ID：</Text>
              <Text>{previewFile.id}</Text>
            </div>
            {previewFile.category_name && (
              <div style={{ marginTop: 8 }}>
                <Text strong>分类：</Text>
                <Text>{previewFile.category_name}</Text>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default LutClusterSnapshots
