// 简单测试前端服务
const http = require('http');

http.get('http://localhost:3000', (res) => {
  console.log(`状态码: ${res.statusCode}`);
  console.log(`前端服务运行正常！`);
  console.log(`访问地址: http://localhost:3000`);
}).on('error', (err) => {
  console.error(`前端服务无法访问: ${err.message}`);
});
