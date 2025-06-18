from evalscope.benchmarks.benchmark import BENCHMARK_MAPPINGS, BenchmarkMeta  
from evalscope.benchmarks.data_adapter import DataAdapter  
from evalscope.constants import OutputType  
import json
from typing import Dict, Any, List, Union
import os.path
from collections import defaultdict
from evalscope.utils.io_utils import jsonl_to_list
from jinja2 import Environment, FileSystemLoader
import os
  
# 动态创建DataAdapter类  
class CustomDatasetAdapter(DataAdapter): 
    def __init__(self, **kwargs):
        # 初始化模板环境
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # 注册自定义过滤器
        self.env.filters['from_json'] = lambda x: json.loads(x) if isinstance(x, str) else x
        self.env.filters['to_json'] = lambda x: json.dumps(x, ensure_ascii=False)
        
        # 加载模板
        template_content = kwargs.get('template_content')
        if not template_content:
            raise ValueError("自定义数据集必须提供 Jinja2 模板内容")
            
        try:
            # 从字符串加载模板
            self.template = self.env.from_string(template_content)
            
            # 验证必需的宏是否存在
            required_macros = ['gen_prompt', 'get_gold_answer', 'match', 'parse_pred_result', 'compute_metric', 'get_config']
            missing_macros = []
            for macro_name in required_macros:
                if not hasattr(self.template.module, macro_name):
                    missing_macros.append(macro_name)
            
            if missing_macros:
                raise ValueError(f"模板缺少以下必需的宏：{', '.join(missing_macros)}")
            
            # 从模板获取配置
            config = json.loads(self.template.module.get_config())
            self.llm_as_a_judge = config.get('llm_as_a_judge', False)
                
        except Exception as e:
            raise ValueError(f"加载 Jinja2 模板失败：{str(e)}")
        
        super().__init__(**kwargs)

    def load(self, dataset_name_or_path: str = None, subset_list: list = None, **kwargs) -> dict:
        dataset_name_or_path = dataset_name_or_path or self.dataset_id
        subset_list = subset_list or self.subset_list

        data_file_dict = defaultdict(str)
        data_item_dict = defaultdict(list)

        # get data file path and subset name
        if os.path.isdir(dataset_name_or_path):
            for subset_name in subset_list:
                data_file_dict[subset_name] = os.path.join(dataset_name_or_path, f'{subset_name}.jsonl')
        elif os.path.isfile(dataset_name_or_path):
            cur_subset_name = os.path.splitext(os.path.basename(dataset_name_or_path))[0]
            data_file_dict[cur_subset_name] = dataset_name_or_path
        else:
            raise ValueError(f'Invalid dataset path: {dataset_name_or_path}')

        # load data from local disk
        try:
            for subset_name, file_path in data_file_dict.items():
                data_item_dict[subset_name] = jsonl_to_list(file_path)
        except Exception as e:
            raise ValueError(f'Failed to load data from {self.dataset_id}, got error: {e}')

        data_dict = {subset_name: {'test': data_item_dict[subset_name]} for subset_name in data_file_dict.keys()}

        return data_dict

    def gen_prompt(self, input_d: dict, subset_name: str, few_shot_list: list, **kwargs):
        try:
            history = input_d.get('history', [])
            system_prompt = input_d.get('system', '')
            user_prompt = input_d.get('question', '') or input_d.get('user', '')
            
            # 使用模板生成提示词
            prompt_result = self.template.module.gen_prompt(
                system_prompt=system_prompt,
                history=history,
                user_prompt=user_prompt
            )
            
            # 解析模板返回的 JSON 字符串
            prompt_dict = json.loads(prompt_result)
            
            return self.gen_prompt_data(
                system_prompt=prompt_dict['system_prompt'],
                prompt=prompt_dict['user_prompt']
            )
        except Exception as e:
            raise ValueError(f"生成提示词失败：{str(e)}")

    def get_gold_answer(self, input_d: dict) -> str:
        try:
            # 使用模板获取标准答案
            return self.template.module.get_gold_answer(input_d=input_d)
        except Exception as e:
            raise ValueError(f"获取标准答案失败：{str(e)}")

    def match(self, gold: str, pred: str) -> dict:
        try:
            # 使用模板比较结果
            result = self.template.module.match(gold=gold, pred=pred)
            return json.loads(result)
        except Exception as e:
            raise ValueError(f"比较结果失败：{str(e)}")

    def parse_pred_result(self, result: str, raw_input_d: dict = None, eval_type: str = 'checkpoint') -> str:
        try:
            # 使用模板解析预测结果
            return self.template.module.parse_pred_result(result=result)
        except Exception as e:
            raise ValueError(f"解析预测结果失败：{str(e)}")

    def compute_metric(self, review_res_list: Union[List[dict], List[List[dict]]], **kwargs) -> List[dict]:
        try:
            # 使用模板计算指标
            result = self.template.module.compute_metric(review_res_list=review_res_list)
            return json.loads(result)
        except Exception as e:
            raise ValueError(f"计算指标失败：{str(e)}")

    def set_custom_template(self, template_name: str):
        """设置自定义模板
        
        Args:
            template_name: 模板文件名
        """
        try:
            self.template = self.env.get_template(template_name)
        except Exception as e:
            raise ValueError(f"加载模板 {template_name} 失败：{str(e)}")

def register_custom_dataset_benchmark(dataset_id: int):
    """动态注册自定义数据集基准测试
    
    Args:
        dataset_name: 数据集名称，用于生成唯一的基准测试名称
    """
    benchmark_name = f'custom_dataset_{dataset_id}'
    
    # 创建BenchmarkMeta实例
    benchmark_meta = BenchmarkMeta(
        name=benchmark_name,
        dataset_id=benchmark_name,
        data_adapter=CustomDatasetAdapter,
        model_adapter=OutputType.GENERATION,
        subset_list=['default'],
        metric_list=['AverageAccuracy'],
        few_shot_num=0,
        eval_split='test'
    )
    
    # 直接添加到全局注册表
    BENCHMARK_MAPPINGS[benchmark_name] = benchmark_meta
    
    return benchmark_name