import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Tag,
  Typography,
  Modal,
  Row,
  Col,
  Image,
  Pagination,
  Empty
} from 'antd'
import { EyeOutlined, ReloadOutlined } from '@ant-design/icons'
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
      width: 120,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handlePreview(record)}
        >
          查看
        </Button>
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

      {/* 快照详情模态框 */}
      <Modal
        title="快照详情"
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false)
          setPreviewSnapshot(null)
        }}
        footer={null}
        width={1200}
      >
        {previewSnapshot && (
          <div>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Text strong>快照名称：</Text>
                <Text>{previewSnapshot.name}</Text>
              </div>
              {previewSnapshot.description && (
                <div>
                  <Text strong>快照描述：</Text>
                  <Text>{previewSnapshot.description}</Text>
                </div>
              )}
              <div>
                <Text strong>聚类指标：</Text>
                <Tag>{previewSnapshot.metric_name || '未知'}</Tag>
                <Text strong style={{ marginLeft: 16 }}>聚类算法：</Text>
                <Tag>{previewSnapshot.algorithm_name || '未知'}</Tag>
                <Text strong style={{ marginLeft: 16 }}>聚类数：</Text>
                <Tag>{previewSnapshot.n_clusters}</Tag>
              </div>
              <div>
                <Text strong>创建时间：</Text>
                <Text>{previewSnapshot.created_at}</Text>
              </div>

              {previewSnapshot.cluster_data && (
                <div>
                  <Title level={5}>聚类详情</Title>
                  <Row gutter={[16, 16]}>
                    {Object.entries(previewSnapshot.cluster_data).map(([clusterId, clusterInfo]) => (
                      <Col xs={24} sm={12} md={8} lg={6} key={clusterId}>
                        <Card
                          title={`聚类 ${clusterId}`}
                          size="small"
                          style={{ height: '100%' }}
                        >
                          <div style={{ marginBottom: 8 }}>
                            <Text strong>文件数：</Text>
                            <Text>{clusterInfo.file_count || 0}</Text>
                          </div>
                          {clusterInfo.files && clusterInfo.files.length > 0 && (
                            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                              <Row gutter={[8, 8]}>
                                {clusterInfo.files.slice(0, 20).map((file) => (
                                  <Col span={12} key={file.id}>
                                    <Card
                                      size="small"
                                      bodyStyle={{ padding: '8px' }}
                                      cover={
                                        file.thumbnail_path ? (
                                          <Image
                                            src={`/api/lut-files/${file.id}/thumbnail`}
                                            alt={file.original_filename}
                                            style={{ height: '80px', objectFit: 'cover' }}
                                            preview={false}
                                          />
                                        ) : (
                                          <div style={{ height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f5f5f5' }}>
                                            <Text type="secondary" style={{ fontSize: '12px' }}>无缩略图</Text>
                                          </div>
                                        )
                                      }
                                    >
                                      <Text
                                        ellipsis
                                        style={{ fontSize: '11px' }}
                                        title={file.original_filename}
                                      >
                                        {file.original_filename}
                                      </Text>
                                    </Card>
                                  </Col>
                                ))}
                              </Row>
                              {clusterInfo.files.length > 20 && (
                                <div style={{ marginTop: 8, textAlign: 'center' }}>
                                  <Text type="secondary" style={{ fontSize: '12px' }}>
                                    还有 {clusterInfo.files.length - 20} 个文件...
                                  </Text>
                                </div>
                              )}
                            </div>
                          )}
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )}
            </Space>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default LutClusterSnapshots
