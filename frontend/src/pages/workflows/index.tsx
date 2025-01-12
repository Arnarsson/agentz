import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  SimpleGrid,
  Text,
  HStack,
  Icon,
  Badge,
  Progress,
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
  VStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  Flex,
} from '@chakra-ui/react'
import {
  FiPlus,
  FiSearch,
  FiFilter,
  FiMoreVertical,
  FiPlay,
  FiPause,
  FiTrash2,
  FiEdit2,
  FiGitBranch,
  FiCpu,
  FiClock,
  FiCheckCircle,
  FiAlertCircle,
} from 'react-icons/fi'
import MainLayout from '@/components/layout/MainLayout'

const WorkflowCard = ({ workflow, onEdit, onDelete }: any) => {
  const statusColors = {
    running: 'green',
    paused: 'yellow',
    completed: 'blue',
    failed: 'red',
  }

  return (
    <Card>
      <CardBody>
        <HStack justify="space-between" mb="4">
          <HStack>
            <Icon as={FiGitBranch} color="brand.500" boxSize="5" />
            <Box>
              <Text fontWeight="semibold">{workflow.name}</Text>
              <Text fontSize="sm" color="gray.500">{workflow.type}</Text>
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
              <MenuItem icon={<FiEdit2 />} onClick={() => onEdit(workflow)}>Edit</MenuItem>
              <MenuItem icon={<FiTrash2 />} onClick={() => onDelete(workflow)} color="red.400">
                Delete
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>

        <Text noOfLines={2} mb="4" fontSize="sm">
          {workflow.description}
        </Text>

        <VStack spacing="2" align="stretch">
          <HStack justify="space-between">
            <Badge colorScheme={statusColors[workflow.status as keyof typeof statusColors]}>
              {workflow.status}
            </Badge>
            <HStack spacing="1" fontSize="sm" color="gray.500">
              <Icon as={FiCpu} />
              <Text>{workflow.agents_count} agents</Text>
            </HStack>
          </HStack>

          <Progress
            value={workflow.progress}
            size="sm"
            colorScheme={statusColors[workflow.status as keyof typeof statusColors]}
          />

          <HStack justify="space-between" fontSize="sm" color="gray.500">
            <HStack spacing="1">
              <Icon as={FiClock} />
              <Text>{workflow.duration}</Text>
            </HStack>
            <HStack spacing="1">
              <Icon as={workflow.success_rate >= 90 ? FiCheckCircle : FiAlertCircle} />
              <Text>{workflow.success_rate}% success</Text>
            </HStack>
          </HStack>
        </VStack>
      </CardBody>
    </Card>
  )
}

const CreateWorkflowModal = ({ isOpen, onClose }: any) => {
  const toast = useToast()
  const [activeTab, setActiveTab] = useState(0)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement workflow creation
    toast({
      title: 'Workflow created.',
      description: "We've created your workflow for you.",
      status: 'success',
      duration: 5000,
      isClosable: true,
    })
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl">
      <ModalOverlay />
      <ModalContent as="form" onSubmit={handleSubmit}>
        <ModalHeader>Create New Workflow</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Tabs index={activeTab} onChange={setActiveTab}>
            <TabList>
              <Tab>Basic Info</Tab>
              <Tab>Agents</Tab>
              <Tab>Process</Tab>
              <Tab>Configuration</Tab>
            </TabList>

            <TabPanels>
              <TabPanel>
                <VStack spacing="4">
                  <FormControl isRequired>
                    <FormLabel>Name</FormLabel>
                    <Input placeholder="Enter workflow name" />
                  </FormControl>

                  <FormControl isRequired>
                    <FormLabel>Description</FormLabel>
                    <Textarea placeholder="Describe the workflow's purpose and expected outcomes" />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Process Type</FormLabel>
                    <Select defaultValue="sequential">
                      <option value="sequential">Sequential</option>
                      <option value="hierarchical">Hierarchical</option>
                      <option value="event_driven">Event-Driven</option>
                      <option value="custom">Custom</option>
                    </Select>
                  </FormControl>
                </VStack>
              </TabPanel>

              <TabPanel>
                <Text>Agent selection and configuration will go here</Text>
              </TabPanel>

              <TabPanel>
                <Text>Process designer will go here</Text>
              </TabPanel>

              <TabPanel>
                <Text>Advanced configuration options will go here</Text>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button
            colorScheme="brand"
            type="submit"
            isDisabled={activeTab < 3}
          >
            Create Workflow
          </Button>
          {activeTab < 3 && (
            <Button
              ml={3}
              onClick={() => setActiveTab(activeTab + 1)}
            >
              Next
            </Button>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

export default function WorkflowsPage() {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [workflows] = useState([
    {
      id: 1,
      name: 'Data Analysis Pipeline',
      type: 'Sequential',
      description: 'End-to-end data processing and analysis workflow with multiple stages.',
      status: 'running',
      progress: 75,
      agents_count: 3,
      duration: '2h 15m',
      success_rate: 95,
    },
    {
      id: 2,
      name: 'Content Generation',
      type: 'Hierarchical',
      description: 'Automated content creation and optimization workflow.',
      status: 'paused',
      progress: 45,
      agents_count: 4,
      duration: '1h 30m',
      success_rate: 88,
    },
    // Add more mock workflows as needed
  ])

  const handleEdit = (workflow: any) => {
    // TODO: Implement edit functionality
    console.log('Edit workflow:', workflow)
  }

  const handleDelete = (workflow: any) => {
    // TODO: Implement delete functionality
    console.log('Delete workflow:', workflow)
  }

  return (
    <MainLayout>
      <Box maxW="7xl" mx="auto">
        {/* Header */}
        <HStack justify="space-between" mb="6">
          <Heading size="lg">Workflows</Heading>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="brand"
            onClick={onOpen}
          >
            Create Workflow
          </Button>
        </HStack>

        {/* Filters */}
        <HStack mb="6" spacing="4">
          <InputGroup maxW="xs">
            <InputLeftElement pointerEvents="none">
              <FiSearch />
            </InputLeftElement>
            <Input placeholder="Search workflows" />
          </InputGroup>

          <Select placeholder="Status" maxW="xs">
            <option value="running">Running</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </Select>

          <Select placeholder="Type" maxW="xs">
            <option value="sequential">Sequential</option>
            <option value="hierarchical">Hierarchical</option>
            <option value="event_driven">Event-Driven</option>
          </Select>

          <IconButton
            aria-label="More filters"
            icon={<FiFilter />}
            variant="ghost"
          />
        </HStack>

        {/* Workflow Grid */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing="4">
          {workflows.map((workflow) => (
            <WorkflowCard
              key={workflow.id}
              workflow={workflow}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </SimpleGrid>

        {/* Create Workflow Modal */}
        <CreateWorkflowModal isOpen={isOpen} onClose={onClose} />
      </Box>
    </MainLayout>
  )
} 