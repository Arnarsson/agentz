import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  HStack,
  Icon,
  Progress,
  List,
  ListItem,
  Badge,
  useColorModeValue,
  Flex,
} from '@chakra-ui/react'
import { FiCpu, FiGitBranch, FiActivity, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'
import MainLayout from '@/components/layout/MainLayout'

const StatCard = ({ label, value, helpText, icon, trend }: any) => {
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
            <StatHelpText>{helpText}</StatHelpText>
          </Stat>
        </HStack>
      </CardBody>
    </Card>
  )
}

const ActivityItem = ({ title, time, status, type }: any) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'green'
      case 'in progress':
        return 'blue'
      case 'failed':
        return 'red'
      default:
        return 'gray'
    }
  }

  return (
    <ListItem py="3">
      <HStack justify="space-between">
        <HStack spacing="4">
          <Icon
            as={status === 'completed' ? FiCheckCircle : FiAlertCircle}
            color={`${getStatusColor(status)}.500`}
          />
          <Box>
            <Text fontWeight="medium">{title}</Text>
            <Text fontSize="sm" color="gray.500">{time}</Text>
          </Box>
        </HStack>
        <Badge colorScheme={getStatusColor(status)}>{status}</Badge>
      </HStack>
    </ListItem>
  )
}

export default function Dashboard() {
  return (
    <MainLayout>
      <Box maxW="7xl" mx="auto">
        {/* Stats Overview */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing="4" mb="8">
          <StatCard
            label="Active Agents"
            value="12"
            helpText="+2 from last week"
            icon={FiCpu}
          />
          <StatCard
            label="Running Workflows"
            value="8"
            helpText="3 completing soon"
            icon={FiGitBranch}
          />
          <StatCard
            label="Tasks Completed"
            value="234"
            helpText="Last 30 days"
            icon={FiCheckCircle}
          />
          <StatCard
            label="System Load"
            value="42%"
            helpText="Well optimized"
            icon={FiActivity}
          />
        </SimpleGrid>

        {/* Main Content */}
        <SimpleGrid columns={{ base: 1, lg: 2 }} spacing="4">
          {/* Active Workflows */}
          <Card>
            <CardHeader>
              <Heading size="md">Active Workflows</Heading>
            </CardHeader>
            <CardBody>
              <List spacing="3">
                <ListItem>
                  <Text fontWeight="medium">Data Analysis Pipeline</Text>
                  <Progress value={80} size="sm" colorScheme="brand" mt="2" />
                  <Text fontSize="sm" color="gray.500" mt="1">
                    80% complete • 2 agents involved
                  </Text>
                </ListItem>
                <ListItem>
                  <Text fontWeight="medium">Content Generation</Text>
                  <Progress value={45} size="sm" colorScheme="brand" mt="2" />
                  <Text fontSize="sm" color="gray.500" mt="1">
                    45% complete • 3 agents involved
                  </Text>
                </ListItem>
                <ListItem>
                  <Text fontWeight="medium">Market Research</Text>
                  <Progress value={20} size="sm" colorScheme="brand" mt="2" />
                  <Text fontSize="sm" color="gray.500" mt="1">
                    20% complete • 4 agents involved
                  </Text>
                </ListItem>
              </List>
            </CardBody>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <Heading size="md">Recent Activity</Heading>
            </CardHeader>
            <CardBody>
              <List spacing="3">
                <ActivityItem
                  title="Data Analysis Complete"
                  time="2 minutes ago"
                  status="completed"
                  type="workflow"
                />
                <ActivityItem
                  title="New Agent Deployed"
                  time="15 minutes ago"
                  status="completed"
                  type="agent"
                />
                <ActivityItem
                  title="Content Generation"
                  time="1 hour ago"
                  status="in progress"
                  type="workflow"
                />
                <ActivityItem
                  title="API Integration Failed"
                  time="2 hours ago"
                  status="failed"
                  type="task"
                />
              </List>
            </CardBody>
          </Card>
        </SimpleGrid>
      </Box>
    </MainLayout>
  )
} 