import {
  Box,
  SimpleGrid,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  HStack,
  Icon,
  Select,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react'
import {
  FiTrendingUp,
  FiCpu,
  FiGitBranch,
  FiCheckCircle,
  FiAlertCircle,
  FiClock,
} from 'react-icons/fi'
import MainLayout from '@/components/layout/MainLayout'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const lineChartData = [
  { name: 'Mon', tasks: 12, success: 10, agents: 5 },
  { name: 'Tue', tasks: 19, success: 15, agents: 6 },
  { name: 'Wed', tasks: 15, success: 13, agents: 5 },
  { name: 'Thu', tasks: 22, success: 20, agents: 7 },
  { name: 'Fri', tasks: 25, success: 22, agents: 7 },
  { name: 'Sat', tasks: 18, success: 16, agents: 6 },
  { name: 'Sun', tasks: 15, success: 14, agents: 5 },
]

const pieChartData = [
  { name: 'Data Analysis', value: 35 },
  { name: 'Content Gen', value: 25 },
  { name: 'Research', value: 20 },
  { name: 'Other', value: 20 },
]

const COLORS = ['#0ea5e9', '#d946ef', '#10b981', '#6366f1']

const StatCard = ({ label, value, trend, icon }: any) => {
  const cardBg = useColorModeValue('white', 'gray.800')
  const iconBg = useColorModeValue('brand.50', 'brand.900')
  const iconColor = useColorModeValue('brand.500', 'brand.200')

  return (
    <Card bg={cardBg}>
      <CardBody>
        <HStack spacing="4">
          <Box
            p="3"
            bg={iconBg}
            borderRadius="lg"
            color={iconColor}
          >
            <Icon as={icon} boxSize="6" />
          </Box>
          <Stat>
            <StatLabel>{label}</StatLabel>
            <StatNumber>{value}</StatNumber>
            <StatHelpText>
              <StatArrow type={trend >= 0 ? 'increase' : 'decrease'} />
              {Math.abs(trend)}% from last month
            </StatHelpText>
          </Stat>
        </HStack>
      </CardBody>
    </Card>
  )
}

const TopPerformersTable = () => {
  return (
    <Table variant="simple">
      <Thead>
        <Tr>
          <Th>Agent</Th>
          <Th>Tasks</Th>
          <Th>Success Rate</Th>
          <Th>Avg Time</Th>
          <Th>Status</Th>
        </Tr>
      </Thead>
      <Tbody>
        <Tr>
          <Td>Data Analyzer</Td>
          <Td>245</Td>
          <Td>98%</Td>
          <Td>1.2s</Td>
          <Td><Badge colorScheme="green">Active</Badge></Td>
        </Tr>
        <Tr>
          <Td>Content Writer</Td>
          <Td>189</Td>
          <Td>95%</Td>
          <Td>2.5s</Td>
          <Td><Badge colorScheme="green">Active</Badge></Td>
        </Tr>
        <Tr>
          <Td>Research Assistant</Td>
          <Td>156</Td>
          <Td>92%</Td>
          <Td>3.1s</Td>
          <Td><Badge colorScheme="yellow">Idle</Badge></Td>
        </Tr>
      </Tbody>
    </Table>
  )
}

export default function AnalyticsPage() {
  const chartTextColor = useColorModeValue('#1a202c', '#e2e8f0')

  return (
    <MainLayout>
      <Box maxW="7xl" mx="auto">
        {/* Header */}
        <HStack justify="space-between" mb="6">
          <Heading size="lg">Analytics</Heading>
          <Select maxW="xs" defaultValue="7d">
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </Select>
        </HStack>

        {/* Stats Overview */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing="4" mb="8">
          <StatCard
            label="Total Tasks"
            value="1,284"
            trend={12}
            icon={FiTrendingUp}
          />
          <StatCard
            label="Active Agents"
            value="15"
            trend={8}
            icon={FiCpu}
          />
          <StatCard
            label="Success Rate"
            value="95.2%"
            trend={3}
            icon={FiCheckCircle}
          />
          <StatCard
            label="Avg Response Time"
            value="1.8s"
            trend={-5}
            icon={FiClock}
          />
        </SimpleGrid>

        {/* Charts */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing="4" mb="8">
          <Card>
            <CardHeader>
              <Heading size="md">Task Performance</Heading>
            </CardHeader>
            <CardBody>
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke={chartTextColor} />
                    <YAxis stroke={chartTextColor} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="tasks" stroke="#0ea5e9" />
                    <Line type="monotone" dataKey="success" stroke="#10b981" />
                    <Line type="monotone" dataKey="agents" stroke="#d946ef" />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <Heading size="md">Task Distribution</Heading>
            </CardHeader>
            <CardBody>
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Detailed Analysis */}
        <Card>
          <CardHeader>
            <Heading size="md">Detailed Analysis</Heading>
          </CardHeader>
          <CardBody>
            <Tabs>
              <TabList>
                <Tab>Top Performers</Tab>
                <Tab>Resource Usage</Tab>
                <Tab>Error Analysis</Tab>
              </TabList>

              <TabPanels>
                <TabPanel>
                  <TopPerformersTable />
                </TabPanel>
                <TabPanel>
                  <Text>Resource usage analysis will go here</Text>
                </TabPanel>
                <TabPanel>
                  <Text>Error analysis will go here</Text>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardBody>
        </Card>
      </Box>
    </MainLayout>
  )
} 