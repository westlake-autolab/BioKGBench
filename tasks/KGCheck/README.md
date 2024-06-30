# Intro
We propose a biomedical knowledge-graph agent BKGAgent, a multi-agent framework based on LangGraph, which is capable of retrieving information in knowledge graph and cross-validate its correctness with multiple information sources.  
Our framework is comprised of three agents, namely the team leader for the progress control, the KG agent for the information retrieval in KG, and the validation agent for checking the correctness of the information from KG, simulating the workflow of a human research team where a leader supervises the assistants' work and makes the final decision given the feedback from them. Besides, the tool executor is solely responsible for executing the tool agent specified.  
When a user assigns a task, the leader initially breaks down the task and announces the plan. Then the KG agent is activated to retrieve task-related information from the KG. This involves specifying the tool and its arguments to the tool executor, interpreting the tool result, and communicating it back to the leader. After that, the validation agent is called for verification with a similar workflow to that of the KG agent. Finally, a conclusion will be drawn by the leader and returned to the user.  
![kgcheck framework](/assets/img/kgcheck-framwork.png "kgcheck framework")
# Code Framework
```
KGCheck  
|-- README.md  
|-- evalutation
|   `-- evaluate.py
|-- kg_toolbox                              # KG tool box
|   `-- kg_tools.py                         # KG tools
|-- retrieve_toolbox
|   |-- __init__.py
|   |-- corpus_based_retrieve.py
|   `-- web_api.py
|-- agents.py                               # Define multi Agents(Leader, KG, Validation, Tool Executor)
|-- prompts.py                              # Define prompts for the agents
|-- team.py                                 # Main script
|-- run_evel.py                             # run eveluation script
`-- tool_box.py
```
# Performance
The experiment results including both process and final answer are shown below.
- assistant agent tool selection rate
    The ratio of using the correct tool in all executions. 
- assistant agent executability
    The ratio of the agent being successfully invoked in all executions.
- EM for final result
    The ratio of support/refute conclusions being consistent with labels in all executions.
- executability for final result
    The ratio of the times the leader gave conclusive replies out of all executions.

<table width="1780.92" border="0" cellpadding="0" cellspacing="0" style="width:763.25pt;border-collapse:collapse;table-layout:fixed;">
   <colgroup><col width="299.02" class="xl65" style="mso-width-source:userset;mso-width-alt:6248;">
   <col width="246.98" span="6" class="xl65" style="mso-width-source:userset;mso-width-alt:5161;">
   <col width="111.53" span="16377" class="xl65" style="mso-width-source:userset;mso-width-alt:2330;">
   </colgroup><tbody><tr height="33.95" style="height:14.55pt;">
    <td class="xl66" height="67.90" width="299.02" rowspan="2" style="height:29.10pt;width:128.15pt;border-right:none;border-bottom:.5pt solid windowtext;" x:str="">model</td>
    <td class="xl67" width="493.97" colspan="2" style="width:211.70pt;border-right:none;border-bottom:.5pt solid windowtext;" x:str="">KG query task</td>
    <td class="xl67" width="493.97" colspan="2" style="width:211.70pt;border-right:none;border-bottom:.5pt solid windowtext;" x:str="">validation task</td>
    <td class="xl67" width="493.97" colspan="2" style="width:211.70pt;border-right:none;border-bottom:.5pt solid windowtext;" x:str="">final result</td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl70" x:str="">tool selection</td>
    <td class="xl70" x:str="">executability</td>
    <td class="xl70" x:str="">tool selection</td>
    <td class="xl70" x:str="">executability</td>
    <td class="xl70" x:str="">Exact Match</td>
    <td class="xl70" x:str="">executability</td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl70" height="33.95" colspan="7" style="height:14.55pt;border-right:none;border-bottom:.5pt solid windowtext;" x:str="">task type: web database KG check</td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl72" height="33.95" style="height:14.55pt;" x:str="">GPT-4</td>
    <td class="xl73" x:num="65.">65.00<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="65.">65.00<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="88.099999999999994">88.10<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="88.799999999999997">88.80<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="64.5">64.50<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="96.900000000000006">96.90<span style="mso-spacerun:yes;">&nbsp;</span></td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl72" height="33.95" style="height:14.55pt;" x:str="">Llama-3-70B-Instruct</td>
    <td class="xl73" x:num="96.900000000000006">96.90<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="96.900000000000006">96.90<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="97.5">97.50<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="97.5">97.50<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="38.100000000000001">38.10<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="100.">100.00<span style="mso-spacerun:yes;">&nbsp;</span></td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl67" height="33.95" colspan="7" style="height:14.55pt;border-right:none;border-bottom:.5pt solid windowtext;" x:str="">task type: publication database KG check</td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl72" height="33.95" style="height:14.55pt;" x:str="">GPT-4</td>
    <td class="xl73" x:num="67.700000000000003">67.70<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="67.700000000000003">67.70<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="69.200000000000003">69.20<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="69.200000000000003">69.20<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="61.5">61.50<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl73" x:num="95.400000000000006">95.40<span style="mso-spacerun:yes;">&nbsp;</span></td>
   </tr>
   <tr height="33.95" style="height:14.55pt;">
    <td class="xl70" height="33.95" style="height:14.55pt;" x:str="">Llama-3-70B-Instruct</td>
    <td class="xl74" x:num="100.">100.00<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl74" x:num="100.">100.00<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl74" x:num="95.400000000000006">95.40<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl74" x:num="95.400000000000006">95.40<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl74" x:num="41.5">41.50<span style="mso-spacerun:yes;">&nbsp;</span></td>
    <td class="xl74" x:num="63.100000000000001">63.10<span style="mso-spacerun:yes;">&nbsp;</span></td>
   </tr>
   <!--[if supportMisalignedColumns]-->
    <tr width="0" style="display:none;">
     <td width="299" style="width:128;"></td>
     <td width="247" style="width:106;"></td>
     <td width="112" style="width:48;"></td>
    </tr>
   <!--[endif]-->
  </tbody></table>