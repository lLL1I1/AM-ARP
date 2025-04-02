# AM-ARP
This project is constructed based on AgentScope to validate the feasibility of the method proposed in the paper. It consists of two main parts:

Part I Code Description:
    The first part verifies the complete requirements process, demonstrating the model's feasibility through natural language requirements processing, requirements modeling, and specification generation. File read/write operations are used to implement requirements traceability, validating the automated multi-agent process proposed in the method. Key implementations include:
     agents directory contains constructed agents:Decomposer: Decomposes original requirements to build structured user requirements. Agent groups (use_case_generator, class_generator, sequence_generator) for UML model analysis and modeling. Document_writer automates requirement specification generation. Prototype validation uses Alibaba's Tongyi Wanxiang (AI model), completing the automated multi-agent process. Requirements modeling utilizes agent groups organized in workflows, with three workflow categories implemented in the workflow directory.

Part II Code Description:
    The second part validates requirements/model change management based on the traceability matrix from original requirements. Implemented via dynamic_workflow, it demonstrates two iterations of requirement updates and automated model element identification for requirement evolution.
