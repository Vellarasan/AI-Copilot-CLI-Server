# Component Test Generation with IntelliJ Copilot Agent Mode

## Project Objective

Develop an intelligent test generation system for IntelliJ IDEA using GitHub Copilot in Agent Mode that automatically generates comprehensive component tests for controller classes. The system will intelligently mock external dependencies (databases like Cassandra/SQL and web APIs) using predefined mock services from a library, guided by project-specific configuration files that define mockable dependencies and repository structure.

## Success Criteria

- Developers can open any controller class and request component test generation through Copilot
- Generated tests automatically mock all external dependencies using the configured mock library
- Tests are contextually aware of the repository structure and follow project conventions
- Minimal manual intervention required; tests are production-ready or near-production-ready
- Consistent test quality across different controllers and team members

---

## Required Tasks

### 1. Design Constitution Files

#### 1.1 Dependency Configuration File (`test-dependencies-config.yaml`)
**Purpose:** Define which external dependencies can be mocked and how to mock them

**Required Content:**
- List of mockable dependencies (databases, APIs, message queues, etc.)
- Mapping of dependency types to mock service implementations
- Mock library details (class names, import statements, initialization patterns)
- Configuration for each dependency type:
  - Connection parameters to mock
  - Common mock behaviors (success/failure scenarios)
  - Data fixtures or test data patterns

**Example Structure:**
```yaml
dependencies:
  databases:
    - type: cassandra
      mock_service: CassandraMockService
      mock_library: com.company.testing.mocks.CassandraMock
      initialization_pattern: "@MockBean CassandraMockService cassandraMock"
      
  external_apis:
    - name: PaymentAPI
      mock_service: PaymentApiMock
      base_url_pattern: "payment.api.baseUrl"
```

#### 1.2 Repository Structure File (`repo-structure-config.yaml`)
**Purpose:** Provide Copilot with understanding of project organization

**Required Content:**
- Directory structure and naming conventions
- Package organization (controllers, services, repositories, models)
- Test directory layout and naming patterns
- Common patterns for dependencies (where repositories are typically injected)
- Configuration file locations
- Test utilities and helper classes location

**Example Structure:**
```yaml
structure:
  source_root: src/main/java
  test_root: src/test/java
  
  patterns:
    controllers: "**/controller/**/*Controller.java"
    services: "**/service/**/*Service.java"
    repositories: "**/repository/**/*Repository.java"
    
  test_conventions:
    naming: "{ClassName}ComponentTest.java"
    base_package_mapping: "same_as_source"
    annotations: ["@SpringBootTest", "@AutoConfigureMockMvc"]
```

---

### 2. Develop Copilot Prompts/Scripts

#### 2.1 Master Prompt Template
**Purpose:** Primary instruction set for Copilot to generate component tests

**Key Components:**
- Introduction to the task (component test generation)
- Instructions to read and parse both constitution files
- Guidelines for analyzing the controller class
- Step-by-step test generation process
- Code quality and best practices requirements

#### 2.2 Context-Building Prompts
**Purpose:** Help Copilot understand the specific controller context

**Tasks:**
- Prompt to identify all dependencies in the controller
- Prompt to map dependencies to mock configurations
- Prompt to analyze controller endpoints and methods
- Prompt to identify request/response patterns

#### 2.3 Test Generation Prompts
**Purpose:** Generate specific test components

**Individual Prompts for:**
- Test class setup and annotations
- Mock bean declarations and initialization
- Test method scaffolding for each endpoint
- Mock behavior configuration (given-when-then patterns)
- Assertion generation based on expected responses
- Edge case and error scenario tests

#### 2.4 Verification Prompts
**Purpose:** Ensure generated tests meet quality standards

**Checklist Prompts:**
- Verify all dependencies are mocked
- Verify test coverage for all public methods
- Check for proper test isolation
- Validate assertion completeness

---

### 3. Implementation Requirements

#### 3.1 Copilot Agent Mode Configuration
- Configure IntelliJ plugin settings for agent mode
- Set up context window to include constitution files
- Define triggers and commands for test generation
- Configure file watchers for constitution file changes

#### 3.2 Prompt Engineering Strategy
- Design prompts to be specific and unambiguous
- Include examples of expected output
- Build in error handling and edge cases
- Create modular prompts that can be composed

#### 3.3 Integration Points
- Define how constitution files are discovered in the project
- Set up workspace awareness for file navigation
- Configure output directory resolution
- Establish naming convention enforcement

---

### 4. Testing & Validation

#### 4.1 Test the Test Generator
- Validate generated tests against various controller types
- Ensure mocks are properly configured
- Verify tests actually run and pass
- Check code quality and maintainability

#### 4.2 Edge Cases to Handle
- Controllers with no dependencies
- Controllers with dependencies not in mock configuration
- Complex nested dependencies
- Controllers using multiple databases
- Async/reactive controllers

#### 4.3 Documentation
- User guide for setting up constitution files
- Instructions for invoking test generation
- Troubleshooting guide
- Best practices for maintaining mock configurations

---

### 5. Refinement & Iteration

#### 5.1 Feedback Loop
- Collect examples of generated tests
- Identify common issues or patterns
- Refine prompts based on output quality
- Update constitution file schemas as needed

#### 5.2 Continuous Improvement
- Add new mock service types as they're developed
- Expand repository structure patterns
- Enhance prompt sophistication
- Build a library of reusable prompt components

---

## Deliverables

1. **Constitution File Schemas** (with examples)
2. **Complete Prompt Library** (master + specialized prompts)
3. **IntelliJ Plugin Configuration Guide**
4. **Sample Generated Tests** (demonstrating various scenarios)
5. **User Documentation**
6. **Maintenance Guide** for updating configurations and prompts

---

## Technology Stack

- **IDE:** IntelliJ IDEA
- **AI Agent:** GitHub Copilot (Agent Mode)
- **Configuration Format:** YAML (or JSON, based on preference)
- **Testing Framework:** JUnit 5 / TestNG (specify your choice)
- **Mock Library:** (Specify: Mockito, WireMock, Testcontainers, etc.)
- **Build Tool:** Maven/Gradle (for test execution validation)

---

## Getting Started

1. Create initial versions of both constitution files
2. Develop the master prompt template
3. Test with a simple controller class
4. Iterate and refine based on results
5. Expand to cover more complex scenarios