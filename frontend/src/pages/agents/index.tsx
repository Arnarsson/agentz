import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardHeader,
  CardBody,
  Heading,
  SimpleGrid,
  Text,
  HStack,
  Icon,
  Badge,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Textarea,
  Switch,
  VStack,
  useToast,
} from '@chakra-ui/react'
import {
  FiPlus,
  FiSearch,
  FiFilter,
  FiMoreVertical,
  FiCpu,
  FiPlay,
  FiPause,
  FiTrash2,
  FiEdit2,
} from 'react-icons/fi'
import MainLayout from '@/components/layout/MainLayout'

const AgentCard = ({ agent, onEdit, onDelete }: any) => {
  const statusColors = {
    active: 'green',
    idle: 'yellow',
    error: 'red',
  }

  return (
    <Card>
      <CardBody>
        <HStack justify="space-between" mb="4">
          <HStack>
            <Icon as={FiCpu} color="brand.500" boxSize="5" />
            <Box>
              <Text fontWeight="semibold">{agent.name}</Text>
              <Text fontSize="sm" color="gray.500">{agent.role}</Text>
            </Box>
          </HStack>
          <Menu>
            <MenuButton
              as={IconButton}
              icon={<FiMoreVertical />}
              variant="ghost"
              size="sm"
              aria-label="More options"
            />
            <MenuList>
              <MenuItem icon={<FiPlay />}>Start</MenuItem>
              <MenuItem icon={<FiPause />}>Pause</MenuItem>
              <MenuItem icon={<FiEdit2 />} onClick={() => onEdit(agent)}>Edit</MenuItem>
              <MenuItem icon={<FiTrash2 />} onClick={() => onDelete(agent)} color="red.400">
                Delete
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>

        <Text noOfLines={2} mb="4" fontSize="sm">
          {agent.description}
        </Text>

        <HStack justify="space-between">
          <Badge colorScheme={statusColors[agent.status as keyof typeof statusColors]}>
            {agent.status}
          </Badge>
          <Text fontSize="sm" color="gray.500">
            {agent.tasks_completed} tasks completed
          </Text>
        </HStack>
      </CardBody>
    </Card>
  )
}

const CreateAgentModal = ({ isOpen, onClose }: any) => {
  const toast = useToast()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement agent creation
    toast({
      title: 'Agent created.',
      description: "We've created your agent for you.",
      status: 'success',
      duration: 5000,
      isClosable: true,
    })
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent as="form" onSubmit={handleSubmit}>
        <ModalHeader>Create New Agent</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing="4">
            <FormControl isRequired>
              <FormLabel>Name</FormLabel>
              <Input placeholder="Enter agent name" />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Role</FormLabel>
              <Input placeholder="e.g., Data Analyst, Content Writer" />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Description</FormLabel>
              <Textarea placeholder="Describe the agent's purpose and capabilities" />
            </FormControl>

            <FormControl>
              <FormLabel>Model</FormLabel>
              <Select defaultValue="gpt-4">
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-2">Claude 2</option>
              </Select>
            </FormControl>

            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Allow Delegation</FormLabel>
              <Switch defaultChecked />
            </FormControl>

            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Verbose Mode</FormLabel>
              <Switch defaultChecked />
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="brand" type="submit">
            Create Agent
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

export default function AgentsPage() {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [agents] = useState([
    {
      id: 1,
      name: 'Data Analyzer',
      role: 'Data Analysis',
      description: 'Specialized in processing and analyzing large datasets with advanced statistical methods.',
      status: 'active',
      tasks_completed: 45,
    },
    {
      id: 2,
      name: 'Content Writer',
      role: 'Content Generation',
      description: 'Creates engaging and SEO-optimized content for various platforms and audiences.',
      status: 'idle',
      tasks_completed: 89,
    },
    // Add more mock agents as needed
  ])

  const handleEdit = (agent: any) => {
    // TODO: Implement edit functionality
    console.log('Edit agent:', agent)
  }

  const handleDelete = (agent: any) => {
    // TODO: Implement delete functionality
    console.log('Delete agent:', agent)
  }

  return (
    <MainLayout>
      <Box maxW="7xl" mx="auto">
        {/* Header */}
        <HStack justify="space-between" mb="6">
          <Heading size="lg">Agents</Heading>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="brand"
            onClick={onOpen}
          >
            Create Agent
          </Button>
        </HStack>

        {/* Filters */}
        <HStack mb="6" spacing="4">
          <InputGroup maxW="xs">
            <InputLeftElement pointerEvents="none">
              <FiSearch />
            </InputLeftElement>
            <Input placeholder="Search agents" />
          </InputGroup>

          <Select placeholder="Status" maxW="xs">
            <option value="active">Active</option>
            <option value="idle">Idle</option>
            <option value="error">Error</option>
          </Select>

          <Select placeholder="Role" maxW="xs">
            <option value="analyst">Data Analyst</option>
            <option value="writer">Content Writer</option>
            <option value="researcher">Researcher</option>
          </Select>

          <IconButton
            aria-label="More filters"
            icon={<FiFilter />}
            variant="ghost"
          />
        </HStack>

        {/* Agent Grid */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing="4">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </SimpleGrid>

        {/* Create Agent Modal */}
        <CreateAgentModal isOpen={isOpen} onClose={onClose} />
      </Box>
    </MainLayout>
  )
} 